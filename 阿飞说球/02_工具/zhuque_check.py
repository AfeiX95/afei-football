# -*- coding: utf-8 -*-
"""
朱雀 AIGC 检测(腾讯云 EdgeOne AI网关)——阿飞·赛博聊球 出稿后降AI检测工具
用法:
  python zhuque_check.py --file "文章.md"
  python zhuque_check.py --file "文章.docx" --top 8
  python zhuque_check.py --text "一段文字"
前置:
  1) 腾讯云 EdgeOne(企业版)控制台创建 AI 网关,拿到网关域名 + API Key
  2) 设置环境变量 ZHUQUE_GATEWAY / ZHUQUE_API_KEY,或同目录放 zhuque_config.json:
     {"gateway": "https://xxx", "api_key": "yyy"}
输出:
  整篇 AI 置信度(softmax/ratio) + 三档占比(人工/AI/疑似AI) + 最像AI的段落Top N(定点改写用)
退出码: 0=正常; 2=配置缺失; 3=调用失败
"""
import os
import sys
import json
import argparse
import urllib.request

TOOL_DIR = os.path.dirname(os.path.abspath(__file__))


def load_conf():
    # 优先环境变量, 其次同目录 zhuque_config.json(不入 git)
    gw = os.environ.get('ZHUQUE_GATEWAY')
    key = os.environ.get('ZHUQUE_API_KEY')
    if gw and key:
        return gw.rstrip('/'), key
    cfg_path = os.path.join(TOOL_DIR, 'zhuque_config.json')
    if os.path.exists(cfg_path):
        c = json.load(open(cfg_path, encoding='utf-8'))
        return c['gateway'].rstrip('/'), c['api_key']
    print('❌ 缺配置: 设置 ZHUQUE_GATEWAY / ZHUQUE_API_KEY 环境变量,')
    print('   或在 02_工具/ 下创建 zhuque_config.json: {"gateway": "https://网关域名", "api_key": "密钥"}')
    sys.exit(2)


def read_text(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == '.docx':
        from docx import Document
        d = Document(path)
        parts = [p.text for p in d.paragraphs if p.text.strip()]
        for t in d.tables:
            for row in t.rows:
                for cell in row.cells:
                    if cell.text.strip():
                        parts.append(cell.text.strip())
        return '\n'.join(parts)
    return open(path, encoding='utf-8').read()


def call_zhuque(gateway, key, text):
    """同步调用 zhuque-text, is_merge=false 逐段返回置信度。"""
    body = json.dumps({'text': text, 'is_merge': False}).encode('utf-8')
    req = urllib.request.Request(
        f'{gateway}/v1/providers/zhuque-text/classify',
        data=body,
        headers={
            'Authorization': f'Bearer {key}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        detail = e.read().decode('utf-8', errors='ignore')[:200]
        hints = {
            401: 'API Key 错误或失效,核对 zhuque_config.json',
            403: '该网关未授权 zhuque-text(检查企业版套餐/provider 拼写)',
            429: '触发限流,稍后重试',
        }
        print(f'❌ HTTP {e.code}: {hints.get(e.code, "服务异常")} | {detail}')
        sys.exit(3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--file', help='待检测文件(md/docx/txt)')
    ap.add_argument('--text', help='或直接传一段文字')
    ap.add_argument('--top', type=int, default=6, help='显示最像AI的段落条数(默认6)')
    ap.add_argument('--threshold', type=float, default=0.6,
                    help='段落AI置信度预警阈值(默认0.6)')
    args = ap.parse_args()

    if args.file:
        text = read_text(args.file)
    elif args.text:
        text = args.text
    else:
        ap.error('需要 --file 或 --text')

    # 掐掉图片标记和标题符号,减少噪声
    clean = '\n'.join(
        ln for ln in text.split('\n')
        if not ln.strip().startswith(('![', '(', '*图'))
    )
    gateway, key = load_conf()
    r = call_zhuque(gateway, key, clean)

    if r.get('status') != 'success':
        print('❌ 推理失败:', r.get('msg'))
        sys.exit(3)

    soft = r.get('softmax_confidence', 0)
    ratio = r.get('ratio_confidence', 0)
    lr = r.get('labels_ratio', {})
    human = float(lr.get('0', 0)) * 100
    ai = float(lr.get('1', 0)) * 100
    sus = float(lr.get('2', 0)) * 100

    print('=' * 56)
    print(f'【朱雀检测】整篇AI置信度: softmax={soft:.3f} | ratio={ratio:.3f}')
    print(f'  三档占比: 人工{human:.1f}% / AI {ai:.1f}% / 疑似AI {sus:.1f}%')
    verdict = '✅ 人工特征达标' if soft < 0.5 else ('⚠ 偏AI,建议定点改写' if soft < 0.8 else '❌ 高AI特征,需大改')
    print(f'  判定: {verdict}')
    print('=' * 56)

    segs = r.get('segment_labels') or []
    hits = [s for s in segs if s.get('conf', 0) >= args.threshold and s.get('label') in (1, 2)]
    hits.sort(key=lambda s: -s.get('conf', 0))
    if hits:
        print(f'\n最像AI的段落 Top {min(args.top, len(hits))} (阈值{args.threshold}, 定点改这些即可):')
        for s in hits[:args.top]:
            excerpt = s.get('text', '').strip().replace('\n', ' ')[:60]
            tag = 'AI' if s.get('label') == 1 else '疑似'
            print(f"  [{tag} {s.get('conf', 0):.2f}] {excerpt}…")
    else:
        print(f'\n无置信度≥{args.threshold}的AI嫌疑段落,全文可发。')


if __name__ == '__main__':
    main()
