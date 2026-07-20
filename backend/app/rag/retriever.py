"""
混合检索器 - 向量检索 + BM25关键词检索 + RRF融合
"""
from typing import List, Dict, Any, Optional
from app.rag.vector_store import similarity_search
from app.config import settings


def vector_search(query: str, k: int = 10) -> List[Dict]:
    """向量语义检索"""
    return similarity_search(query, k=k)


def bm25_search(query: str, documents: List[Dict], k: int = 10) -> List[Dict]:
    """
    BM25关键词检索
    documents: 从数据库获取的所有chunk列表
    """
    try:
        from rank_bm25 import BM25Okapi
        import jieba

        # 对所有文档分词
        tokenized_corpus = []
        for doc in documents:
            tokens = list(jieba.cut(doc["content"]))
            tokenized_corpus.append(tokens)

        # 构建BM25索引
        bm25 = BM25Okapi(tokenized_corpus)

        # 查询分词
        query_tokens = list(jieba.cut(query))

        # 获取分数
        scores = bm25.get_scores(query_tokens)

        # 排序取Top-K
        indexed_scores = [(i, score) for i, score in enumerate(scores)]
        indexed_scores.sort(key=lambda x: x[1], reverse=True)

        results = []
        for idx, score in indexed_scores[:k]:
            if score > 0:
                doc = documents[idx]
                results.append({
                    "content": doc["content"],
                    "metadata": {"document_id": doc.get("document_id"), "chunk_index": doc.get("chunk_index")},
                    "score": float(score),
                    "source": "bm25",
                })
        return results
    except ImportError:
        print("[BM25] rank_bm25或jieba未安装，跳过关键词检索")
        return []


def reciprocal_rank_fusion(
    vector_results: List[Dict],
    bm25_results: List[Dict],
    k: int = 60,
    top_k: int = 10,
) -> List[Dict]:
    """
    RRF (Reciprocal Rank Fusion) 融合排序
    k: 平滑参数，默认60
    """
    # 存储每个 content 的累计 RRF 分数
    score_map: Dict[str, float] = {}
    # 存储每个 content 对应的原始结果数据
    data_map: Dict[str, Dict] = {}

    # 向量检索排名
    for rank, result in enumerate(vector_results):
        key = result["content"]
        score_map[key] = score_map.get(key, 0) + 1.0 / (k + rank + 1)
        if key not in data_map:
            data_map[key] = result

    # BM25排名
    for rank, result in enumerate(bm25_results):
        key = result["content"]
        score_map[key] = score_map.get(key, 0) + 1.0 / (k + rank + 1)
        if key not in data_map:
            data_map[key] = result

    # 按分数降序排序
    sorted_keys = sorted(score_map, key=lambda x: score_map[x], reverse=True)

    # 取Top-K
    final_results = []
    for key in sorted_keys[:top_k]:
        result_data = data_map[key].copy()
        result_data["fused_score"] = score_map[key]
        final_results.append(result_data)

    return final_results


def hybrid_retrieve(
    query: str,
    all_chunks: Optional[List[Dict]] = None,
    top_k: int = None,
) -> List[Dict]:
    """
    混合检索主函数
    1. 向量检索 Top-10
    2. BM25检索 Top-10
    3. RRF融合
    4. 返回Top-K
    """
    top_k = top_k or settings.RAG_SEARCH_TOP_K

    # 向量检索
    vector_results = vector_search(query, k=10)

    # BM25检索（如果有全量chunk数据）
    bm25_results = []
    if all_chunks:
        bm25_results = bm25_search(query, all_chunks, k=10)

    # 融合
    if bm25_results:
        fused = reciprocal_rank_fusion(vector_results, bm25_results, top_k=top_k)
    else:
        fused = vector_results[:top_k]

    return fused
