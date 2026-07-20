"""
将 MySQL 中的知识数据索引到 ChromaDB
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.knowledge import KnowledgeDocument, KnowledgeChunk
from app.rag.vector_store import add_documents, delete_all


def index_all():
    db = SessionLocal()
    try:
        # 清空现有索引
        print("[ChromaDB] 清空现有索引...")
        delete_all()

        # 获取所有已索引的文档
        docs = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.status == "indexed"
        ).all()

        print(f"[ChromaDB] 找到 {len(docs)} 个文档需要索引")

        total_chunks = 0
        for doc in docs:
            chunks = db.query(KnowledgeChunk).filter(
                KnowledgeChunk.document_id == doc.id
            ).order_by(KnowledgeChunk.chunk_index).all()

            if not chunks:
                continue

            texts = [chunk.content for chunk in chunks]
            metadatas = [
                {
                    "document_id": doc.id,
                    "doc_title": doc.title,
                    "chunk_index": chunk.chunk_index,
                }
                for chunk in chunks
            ]

            # 添加到 ChromaDB
            ids = add_documents(texts, metadatas)
            total_chunks += len(ids)
            print(f"  - {doc.title}: {len(ids)} 个片段")

        print(f"\n[完成] 共索引 {total_chunks} 个知识片段到 ChromaDB")

    finally:
        db.close()


if __name__ == "__main__":
    index_all()
