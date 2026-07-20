"""
本地向量存储 - 支持 TF-IDF（本地）和 通义千问（云端API）
向量数据完全在内存中，不写任何文件到硬盘
"""
from typing import List, Dict, Any, Optional
import numpy as np
from app.rag.embeddings import get_embeddings
from app.database import SessionLocal
from app.models.knowledge import KnowledgeChunk
from app.config import settings

# 全局向量索引（内存中）
_index_built = False
_chunk_ids: List[int] = []
_chunk_texts: List[str] = []
_chunk_metadatas: List[Dict] = []
_vectors: Optional[np.ndarray] = None
_embeddings = None  # 延迟初始化


def _get_embeddings():
    """获取 embeddings 实例（延迟加载，读取配置）"""
    global _embeddings
    if _embeddings is None:
        _embeddings = get_embeddings(settings.EMBEDDING_PROVIDER)
    return _embeddings


def _build_index():
    """从MySQL加载所有chunk并构建向量索引"""
    global _index_built, _chunk_ids, _chunk_texts, _chunk_metadatas, _vectors

    db = SessionLocal()
    try:
        chunks = db.query(KnowledgeChunk).order_by(KnowledgeChunk.id).all()

        _chunk_ids = [c.id for c in chunks]
        _chunk_texts = [c.content for c in chunks]
        _chunk_metadatas = [
            {
                "document_id": c.document_id,
                "doc_title": c.document.title if c.document else "未知",
                "chunk_index": c.chunk_index,
            }
            for c in chunks
        ]

        if _chunk_texts:
            embeddings = _get_embeddings()
            print(f"[向量索引] 构建中，共 {len(_chunk_texts)} 个片段，提供商: {settings.EMBEDDING_PROVIDER}...")
            vectors_list = embeddings.embed_documents(_chunk_texts)
            _vectors = np.array(vectors_list, dtype=np.float32)
            _index_built = True
            print(f"[向量索引] 构建完成，维度: {_vectors.shape[1]}")
        else:
            embeddings = _get_embeddings()
            dim = getattr(embeddings, 'vector_dim', 1024)
            _vectors = np.array([], dtype=np.float32).reshape(0, dim)
            _index_built = True
            print("[向量索引] 暂无数据")
    finally:
        db.close()


def rebuild_index():
    """重建索引（文档更新后调用）"""
    global _index_built
    _index_built = False
    _build_index()


def add_documents(texts: List[str], metadatas: List[Dict[str, Any]]) -> List[str]:
    """
    添加文档到向量库
    只需重建索引（因为数据已在MySQL中）
    返回: 空列表（无需返回ID）
    """
    rebuild_index()
    return [""] * len(texts)


def similarity_search(query: str, k: int = 10, filter_dict: dict = None) -> List[Dict]:
    """
    余弦相似度搜索
    返回: [{"content": str, "metadata": dict, "score": float}]
    """
    global _index_built
    if not _index_built:
        _build_index()

    if _vectors is None or len(_vectors) == 0:
        return []

    # 查询向量化
    embeddings = _get_embeddings()
    query_vec = np.array(embeddings.embed_query(query), dtype=np.float32)

    # 余弦相似度
    # 归一化
    query_norm = np.linalg.norm(query_vec)
    if query_norm == 0:
        return []
    query_vec_normed = query_vec / query_norm

    # 计算所有向量的相似度
    vec_norms = np.linalg.norm(_vectors, axis=1)
    vec_norms[vec_norms == 0] = 1e-10  # 避免除零
    vectors_normed = _vectors / vec_norms[:, np.newaxis]

    similarities = np.dot(vectors_normed, query_vec_normed)

    # 过滤
    valid_indices = list(range(len(_chunk_ids)))
    if filter_dict and "document_id" in filter_dict:
        target_id = filter_dict["document_id"]
        valid_indices = [i for i, m in enumerate(_chunk_metadatas)
                        if m.get("document_id") == target_id]

    # 排序取Top-K
    valid_similarities = [(i, similarities[i]) for i in valid_indices]
    valid_similarities.sort(key=lambda x: x[1], reverse=True)

    results = []
    for idx, score in valid_similarities[:k]:
        results.append({
            "content": _chunk_texts[idx],
            "metadata": _chunk_metadatas[idx],
            "score": float(score),
        })

    return results


def delete_by_document_id(document_id: int) -> bool:
    """删除文档后重建索引"""
    try:
        rebuild_index()
        return True
    except Exception as e:
        print(f"[向量索引] 删除重建失败: {e}")
        return False


def delete_all() -> bool:
    """清空索引"""
    global _index_built, _chunk_ids, _chunk_texts, _chunk_metadatas, _vectors
    _index_built = False
    _chunk_ids = []
    _chunk_texts = []
    _chunk_metadatas = []
    _vectors = None
    return True


def get_collection_stats() -> Dict:
    """获取索引统计信息"""
    if not _index_built:
        _build_index()
    embeddings = _get_embeddings()
    return {
        "collection_name": f"embedding_{settings.EMBEDDING_PROVIDER}",
        "entity_count": len(_chunk_ids),
        "vector_dim": _vectors.shape[1] if _vectors is not None and len(_vectors) > 0 else 0,
        "provider": settings.EMBEDDING_PROVIDER,
    }
