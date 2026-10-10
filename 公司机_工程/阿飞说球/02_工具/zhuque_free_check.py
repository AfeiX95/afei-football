# -*- coding: utf-8 -*-
"""
朱雀AI检测(免费网页版协议逆向)——阿飞·赛博聊球 出稿降AI检测工具
原理(2026-08-28 从 matrix.tencent.com 前端JS逆向):
  1) WebSocket 连 wss://matrix.tencent.com/ai_gen_txt_server/getClassify
  2) 服务端先下发 access_token(免登录游客身份), 客户端回传 access_token
  3) 客户端发 {"text": "..."} (≥350字); 服务端回 {"code":1,"evil_level":0} = 需要腾讯验证码(ticket)
  4) 人机验证通过后发 {"ticket":..,"randstr":..}, 再发 {"text":..}, 服务端流式返回:
     waiting(排队) → running → success{confidence, segment_labels[{text,label,conf,order}]}
  ⚠ 瓶颈: 每次检测都要过一次腾讯TCaptcha人机验证(code 1/evil_level 0门禁),
    无法纯脚本绕过 → 本工具采用【半自动模式】: websocket直连+token自动握手,
    验证码环节弹出浏览器让用户点一下(每天有免费次数限制, localStorage计数)

用法:
  python zhuque_free_check.py --file "文章.md"     # 打开浏览器辅助验证后自动出结果
  python zhuque_free_check.py --selftest           # 只测连通+token握手
"""
import os
import sys
import json
import argparse
import hashlib
import random
import time

try:
    import websocket  # pip install websocket-client
except ImportError:
    print('缺依赖: pip install websocket-client')
    sys.exit(1)

WS_URL = 'wss://matrix.tencent.com/ai_gen_txt_server/getClassify'
TOOL_DIR = os.path.dirname(os.path.abspath(__file__))


def make_fp():
    """模拟前端 fp: sha256(visitorId_ts_rand)[:32]"""
    s = f"{random.randint(10**15, 10**16)}_{int(time.time()*1000)}_{random.random()}"
    return hashlib.sha256(s.encode()).hexdigest()[:32]


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


class ZhuqueClient:
    def __init__(self):
        self.fp = make_fp()
        self.ws = None
        self.token = None
        self.result = None
        self.need_captcha = False

    def connect(self, timeout=15):
        self.ws = websocket.create_connection(
            WS_URL, timeout=timeout,
            origin='https://matrix.tencent.com',
            header={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0'},
        )
        # 第一条消息: 服务端下发 access_token
        first = json.loads(self.ws.recv())
        if first.get('access_token'):
            self.token = first['access_token']
            self.ws.send(json.dumps({'access_token': self.token}))
            return True
        return False

    def submit(self, text):
        self.ws.send(json.dumps({'text': text}))

    def wait_result(self, on_event=None, max_wait=120):
        """收事件直到 success/failed/limited。返回最终 dict。"""
        start = time.time()
        while time.time() - start < max_wait:
            try:
                msg = json.loads(self.ws.recv())
            except Exception:
                break
            if on_event:
                on_event(msg)
            status = msg.get('status')
            if status == 'success':
                return msg
            if status in ('failed', 'limited'):
                return msg
            if msg.get('code') == 1 and msg.get('evil_level') == 0:
                return {'status': 'need_captcha',
                        'hint': '服务端要求腾讯TCaptcha人机验证(ticket)——网页版防自动化门禁'}
        return {'status': 'timeout'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--file', help='待检测文件(md/docx/txt)')
    ap.add_argument('--text', help='或直接传文字(≥350字)')
    ap.add_argument('--max-wait', type=int, default=120)
    args = ap.parse_args()

    text = read_text(args.file) if args.file else (args.text or '')
    # 去掉图片标记噪声
    text = '\n'.join(ln for ln in text.split('\n')
                     if not ln.strip().startswith(('![', '*图', '(')))
    if len(text.replace(' ', '')) < 350:
        print(f'❌ 文本太短({len(text)}字), 朱雀要求≥350字')
        sys.exit(1)

    c = ZhuqueClient()
    print('连接朱雀 WebSocket...')
    if not c.connect():
        print('❌ 握手失败(未拿到access_token)')
        sys.exit(3)
    print('✓ 握手成功, 提交文本...')
    c.submit(text)

    def show(m):
        s = m.get('status')
        if s == 'waiting':
            print(f"  排队中(剩余{m.get('remaining', '?')}人)...")
        elif s == 'running':
            print('  检测运行中...')

    r = c.wait_result(on_event=show, max_wait=args.max_wait)

    if r.get('status') == 'need_captcha':
        print('\n❌ 卡在腾讯人机验证门禁: 朱雀网页版每次检测都要过TCaptcha滑块,')
        print('   纯脚本无法绕过。两个可行路径:')
        print('   ① 浏览器半自动: 手动在 matrix.tencent.com/ai-detect 网页检测(每次点一下滑块),')
        print('      电脑旁操作1分钟, 结果页有逐段标红, 直接照着改')
        print('   ② 企业API: EdgeOne企业版AI网关(zhuque-text), 无验证码, 走 zhuque_check.py 全自动')
        sys.exit(4)

    if r.get('status') != 'success':
        print('❌ 检测失败:', r.get('msg') or r.get('status'))
        sys.exit(3)

    conf = r.get('confidence', 0)
    segs = r.get('segment_labels') or []
    print('=' * 56)
    print(f'【朱雀检测】整篇AI置信度: {conf:.3f}')
    verdict = '✅ 人工特征达标' if conf < 0.5 else ('⚠ 偏AI,定点改写' if conf < 0.8 else '❌ 高AI特征,需大改')
    print(f'  判定: {verdict}')
    print('=' * 56)
    hits = [s for s in segs if s.get('conf', 0) >= 0.6 and s.get('label') in (1, 2)]
    hits.sort(key=lambda s: -s.get('conf', 0))
    if hits:
        print(f'\n最像AI的段落 Top {min(8, len(hits))} (定点改这些即可):')
        for s in hits[:8]:
            excerpt = s.get('text', '').strip().replace('\n', ' ')[:60]
            tag = 'AI' if s.get('label') == 1 else '疑似'
            print(f"  [{tag} {s.get('conf', 0):.2f}] {excerpt}…")
    else:
        print('\n无高置信AI嫌疑段落, 可发。')


if __name__ == '__main__':
    main()
