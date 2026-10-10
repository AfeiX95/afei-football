# -*- coding: utf-8 -*-
"""阿飞·赛博聊球 知识库核心 — 路径常量 / 索引加载 / 检索函数

被 build_kb.py(构建) / retrieve.py(CLI) / afei_generator.py(注入) 共用。
"""
import json
import os

# 包位置: 阿飞说球/02_工具/kb/ → BASE = 阿飞说球/
BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB_DIR = os.path.join(BASE, '03_参考资料', 'kb_index')
MODEL_DIR = os.path.join(BASE, '03_参考资料', 'kb_models', 'bge-small-zh-v1.5')
ARTICLES_DIR = os.path.join(BASE, '04_赛事文章')

# bge 官方建议: 查询侧加指令前缀, 文档侧不加(检索质量提升明显)
QUERY_PREFIX = '为这个句子生成表示以用于检索相关文章：'

_model = None
_index = None
_chunks = None
_tfidf = None  # (vectorizer, matrix) 关键词检索缓存


def load_kb():
    """懒加载 FAISS 索引 + 块元数据 + 模型, 索引不存在返回 None"""
    global _model, _index, _chunks
    if _index is None:
        import faiss
        idx_path = os.path.join(KB_DIR, 'kb_index.faiss')
        chunk_path = os.path.join(KB_DIR, 'kb_chunks.json')
        if not (os.path.exists(idx_path) and os.path.exists(chunk_path)):
            return None
        with open(idx_path, 'rb') as f:
            raw = f.read()
        import numpy as np
        _index = faiss.deserialize_index(np.frombuffer(raw, dtype='uint8'))
        with open(chunk_path, encoding='utf-8') as f:
            _chunks = json.load(f)
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(MODEL_DIR)
    return _model, _index, _chunks


def _load_tfidf():
    """jieba 分词 + TF-IDF 关键词索引(懒加载, 首次 ~2s, 内存缓存)"""
    global _tfidf
    if _tfidf is None:
        import jieba
        from sklearn.feature_extraction.text import TfidfVectorizer
        _, _, chunks = load_kb()

        def tokenize(t):
            return ' '.join(jieba.cut(t))

        vec = TfidfVectorizer(tokenizer=tokenize, lowercase=False)
        mat = vec.fit_transform([c['text'] for c in chunks])
        _tfidf = (vec, mat)
    return _tfidf


def keyword_search(query, topk=40):
    """关键词检索 → [(块idx, score)] (TfidfVectorizer 已 L2 归一化, dot=cosine)

    section 加权: 信息卡块(仅对阵信息)降权, 赛后复盘块(高价值资产)加权
    """
    import jieba
    _, _, chunks = load_kb()
    vec, mat = _load_tfidf()
    q = vec.transform([' '.join(jieba.cut(query))])
    scores = (mat @ q.T).toarray().ravel()
    for i in range(len(scores)):
        sec = chunks[i]['section']
        if sec == '开头·信息卡':
            scores[i] *= 0.3
        elif sec == '赛后复盘':
            scores[i] *= 1.2
    idx = scores.argsort()[::-1][:topk]
    return [(int(i), float(scores[i])) for i in idx if scores[i] > 0]


def embed(texts, is_query=False):
    """文本→归一化向量 (余弦相似度可直接用 IndexFlatIP)"""
    model, _, _ = load_kb()
    if is_query:
        texts = [QUERY_PREFIX + t for t in texts]
    return model.encode(texts, normalize_embeddings=True)


def kb_search(query, topk=5, is_query=True, hybrid=True):
    """检索历史分析块 → [{score, match, section, text, source}], 索引缺失返回 None

    hybrid=True: 向量(语义) + 关键词(TF-IDF) 双路检索, RRF 融合排序
    hybrid=False: 纯向量(余弦相似度)
    score 在 hybrid 下为 RRF 融合分(非相似度), 越大越相关
    """
    loaded = load_kb()
    if loaded is None:
        return None
    _, index, chunks = loaded
    import numpy as np
    q = embed([query], is_query=is_query)

    VEC_N = 40  # 每路取 top40 再融合
    D, I = index.search(np.asarray(q, dtype='float32'), VEC_N)
    vec_rank = {int(idx): r for r, idx in enumerate(I[0]) if idx >= 0}

    # RRF 融合: 每路按排名贡献 1/(60+rank), 双路命中排名叠加
    rrf = {idx: 1.0 / (60 + r) for idx, r in vec_rank.items()}
    if hybrid:
        kw = keyword_search(query, VEC_N)
        kw_rank = {idx: r for r, (idx, _) in enumerate(kw)}
        for idx, _s in kw:
            rrf[idx] = rrf.get(idx, 0) + 1.0 / (60 + kw_rank[idx])

    top = sorted(rrf.items(), key=lambda kv: -kv[1])[:topk]
    out = []
    for idx, s in top:
        out.append({'score': round(s, 4), **chunks[idx]})
    return out


def match_query(home, away, league='', competition='', extra=''):
    """对阵式查询自动拼检索语句"""
    parts = [home, 'vs', away]
    if league:
        parts.append(league)
    if competition:
        parts.append(competition)
    if extra:
        parts.append(extra)
    return ' '.join(parts)
