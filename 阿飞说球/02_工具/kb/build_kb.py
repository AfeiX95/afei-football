# -*- coding: utf-8 -*-
"""
build_kb.py — 阿飞·赛博聊球 历史分析知识库构建器 v1.0
=====================================================
用法:
    python build_kb.py            # 全量重建(16篇文章约几秒, 无需增量)
    python build_kb.py --rebuild  # 同上(全量重建, 参数保留兼容)

数据源 : 阿飞说球/04_赛事文章/<场次>/*.md (每场一篇赛事前瞻, 串烧文同样入库)
切块   : 按 "## " 二级标题切; 超长小节(>500字)按空行段落再切, 每块带
         [场次名]+小节标题 上下文前缀
向量   : bge-small-zh-v1.5 (modelscope 本地模型, 中文检索), 归一化
索引   : FAISS IndexFlatIP (归一化向量 = 余弦相似度)
输出   : 阿飞说球/03_参考资料/kb_index/
         ├── kb_index.faiss + kb_chunks.json
         └── kb_meta.json (构建信息)
"""
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kb_core import KB_DIR, MODEL_DIR, ARTICLES_DIR

MAX_CHUNK_LEN = 500  # 超过则按段落再切
MIN_CJK_RATIO = 0.20  # 块内中文字符占比下限(过滤英文配图说明等噪音)


def _cjk_ratio(text):
    cjk = sum(1 for ch in text if '\u4e00' <= ch <= '\u9fff')
    return cjk / max(len(text), 1)


def _keep(text):
    return _cjk_ratio(text) >= MIN_CJK_RATIO


def list_articles():
    """递归扫描 04_赛事文章/ (含 <YYYY-MM>/ 归档子目录)
    返回 [(场次名, 内容文件绝对路径)], 优先 md, 无 md 则取 docx"""
    out = []
    if not os.path.isdir(ARTICLES_DIR):
        return out
    for root, dirs, files in os.walk(ARTICLES_DIR):
        if root == ARTICLES_DIR:
            continue  # 只处理月份子目录, 跳过根下的 MOC 等索引文件
        files = [f for f in files if not f.startswith('~$') and '_new' not in f]
        md = sorted(f for f in files if f.endswith('.md'))
        dx = sorted(f for f in files if f.endswith('.docx'))
        if md:
            out.append((os.path.basename(root), os.path.join(root, md[0])))
        elif dx:
            out.append((os.path.basename(root), os.path.join(root, dx[0])))
    return out


def docx_to_text(path):
    """docx → 纯文本 (段落 + 表格), 供无 md 的场次入库"""
    from docx import Document
    doc = Document(path)
    parts = []
    for p in doc.paragraphs:
        t = p.text.strip()
        if t:
            parts.append(t)
    for tbl in doc.tables:
        for row in tbl.rows:
            parts.append(' | '.join(c.text.strip() for c in row.cells))
    # 段落间留空行, 供 chunk_plain 按段切块
    return '\n\n'.join(parts)


def chunk_article(md_path, match_name):
    """md/docx → 块列表 [{text, match, section, source}]"""
    if md_path.endswith('.docx'):
        return chunk_plain(docx_to_text(md_path), match_name, md_path)

    with open(md_path, encoding='utf-8') as f:
        text = f.read()
    if not text.strip():
        return []
    lines = text.split('\n')
    chunks = []
    cur_title = None
    cur_lines = []

    def flush():
        if not cur_lines:
            return
        body = '\n'.join(cur_lines).strip()
        if not body:
            return
        sec = cur_title or '开头·信息卡'
        # 表格/短行堆叠的正文可能没空行分隔, 长度超限时按 "| " 表格行保护切段
        if len(body) > MAX_CHUNK_LEN:
            for para in re.split(r'\n\s*\n', body):
                para = para.strip()
                if para and _keep(para):
                    chunks.append({
                        'text': f'[{match_name}] {sec}\n{para}',
                        'match': match_name, 'section': sec,
                        'source': os.path.relpath(md_path, ARTICLES_DIR),
                    })
        else:
            if _keep(body):
                chunks.append({
                    'text': f'[{match_name}] {sec}\n{body}',
                    'match': match_name, 'section': sec,
                    'source': os.path.relpath(md_path, ARTICLES_DIR),
                })

    for line in lines:
        if line.startswith('## '):
            flush()
            cur_title = line[3:].strip()
            cur_lines = []
        elif line.startswith('# '):
            continue  # 主标题已体现在 match_name
        else:
            cur_lines.append(line)
    flush()
    return chunks


def chunk_plain(text, match_name, src_path):
    """无章节标记的纯文本(docx) → 按段落切块"""
    chunks = []
    for para in re.split(r'\n\s*\n', text):
        para = para.strip()
        if para and _keep(para):
            chunks.append({
                'text': f'[{match_name}] 正文段落\n{para}',
                'match': match_name, 'section': '正文段落',
                'source': os.path.relpath(src_path, ARTICLES_DIR),
            })
    return chunks


def main():
    t0 = time.time()
    articles = list_articles()
    if not articles:
        print('⚠ 未找到任何赛事前瞻文章, 请确认 04_赛事文章/ 下有 <场次>/<场次>_赛事前瞻.md')
        return 1
    print(f'扫描到 {len(articles)} 篇文章')

    chunks = []
    for match_name, md_path in articles:
        cs = chunk_article(md_path, match_name)
        chunks.extend(cs)
        print(f'  {match_name}: {len(cs)} 块')
    # 追加赛后复盘块(reviews/ 留档, 全量重建不丢增量资产)
    from kb_core import BASE as KB_BASE
    reviews_dir = os.path.join(os.path.dirname(KB_BASE), '00_引擎', 'backtest', 'reviews')
    n_rev = 0
    if os.path.isdir(reviews_dir):
        for fn in sorted(os.listdir(reviews_dir)):
            if not fn.endswith('.json'):
                continue
            with open(os.path.join(reviews_dir, fn), encoding='utf-8') as f:
                r = json.load(f)
            chunks.append({
                'text': r['review_text'],
                'match': r['match'], 'section': '赛后复盘',
                'source': os.path.join('00_引擎', 'backtest', 'reviews', fn),
            })
            n_rev += 1
        print(f'  赛后复盘: {n_rev} 块')
    print(f'共 {len(chunks)} 个知识块')

    # 向量化
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(MODEL_DIR)
    texts = [c['text'] for c in chunks]
    print(f'向量化 {len(texts)} 块 (模型: {os.path.basename(MODEL_DIR)}) ...')
    emb = model.encode(texts, normalize_embeddings=True, show_progress_bar=True)

    # FAISS 索引
    import faiss
    import numpy as np
    index = faiss.IndexFlatIP(emb.shape[1])
    index.add(np.asarray(emb, dtype='float32'))
    os.makedirs(KB_DIR, exist_ok=True)
    # 注意: faiss.write_index 底层用 C fopen, Windows 中文路径会失败
    # 改用 serialize_index 字节流 + Python 写文件(宽字符 API)绕开
    with open(os.path.join(KB_DIR, 'kb_index.faiss'), 'wb') as f:
        f.write(faiss.serialize_index(index))
    with open(os.path.join(KB_DIR, 'kb_chunks.json'), 'w', encoding='utf-8') as f:
        json.dump(chunks, f, ensure_ascii=False, indent=1)
    meta = {
        'build_time': time.strftime('%Y-%m-%d %H:%M:%S'),
        'articles': len(articles),
        'chunks': len(chunks),
        'model': MODEL_DIR,
        'dim': int(emb.shape[1]),
        'chunk_len_limit': MAX_CHUNK_LEN,
    }
    with open(os.path.join(KB_DIR, 'kb_meta.json'), 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)

    print(f'✔ 知识库构建完成: {KB_DIR}')
    print(f'  索引维度 {emb.shape[1]} | 耗时 {time.time()-t0:.1f}s | 文章 {len(articles)} 篇 / 块 {len(chunks)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
