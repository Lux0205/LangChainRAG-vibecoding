"""知识库服务 - 文档上传、索引、删除"""
import os
import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException
from app.models.knowledge import KnowledgeDocument, KnowledgeChunk
from app.models.user import User
from app.rag.document_loader import process_file
from app.rag.vector_store import add_documents, delete_by_document_id, delete_all
from app.config import settings


class KnowledgeService:

    @staticmethod
    async def upload_document(
        db: Session,
        file: UploadFile,
        user: User,
    ) -> KnowledgeDocument:
        """上传并索引知识文档"""
        # 确定文件类型
        filename = file.filename or "unknown"
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        supported_types = ["pdf", "docx", "txt", "csv"]
        if ext not in supported_types:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: {ext}，支持: {supported_types}",
            )

        # 保存文件
        file_id = str(uuid.uuid4())[:8]
        safe_filename = f"{file_id}_{filename}"
        file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)

        content = await file.read()
        if len(content) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=400, detail="文件超过大小限制(50MB)")

        with open(file_path, "wb") as f:
            f.write(content)

        # 创建数据库记录
        doc = KnowledgeDocument(
            title=filename,
            content="",  # 稍后更新
            file_path=file_path,
            file_type=ext,
            status="processing",
            uploaded_by=user.id,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        try:
            # 加载和切分
            raw_text, chunks = process_file(file_path, ext)

            # 更新文档内容
            doc.content = raw_text[:10000]  # 限制存储长度
            doc.chunk_count = len(chunks)

            # 向量化并写入Milvus
            metadatas = [
                {
                    "document_id": doc.id,
                    "doc_title": filename,
                    "chunk_index": i,
                }
                for i in range(len(chunks))
            ]
            milvus_ids = add_documents(chunks, metadatas)

            # 保存chunk记录
            for i, (chunk_text, milvus_id) in enumerate(zip(chunks, milvus_ids)):
                chunk_record = KnowledgeChunk(
                    document_id=doc.id,
                    content=chunk_text,
                    milvus_id=milvus_id,
                    chunk_index=i,
                )
                db.add(chunk_record)

            doc.status = "indexed"
            db.commit()
            db.refresh(doc)

        except Exception as e:
            doc.status = "failed"
            db.commit()
            raise HTTPException(status_code=500, detail=f"文档索引失败: {str(e)}")

        return doc

    @staticmethod
    def get_documents(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        keyword: str = None,
    ) -> dict:
        """获取文档列表（分页）"""
        query = db.query(KnowledgeDocument)

        if keyword:
            query = query.filter(KnowledgeDocument.title.contains(keyword))

        total = query.count()
        docs = query.order_by(KnowledgeDocument.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [doc.to_dict() for doc in docs],
        }

    @staticmethod
    def delete_document(db: Session, doc_id: int) -> bool:
        """删除文档（同步删除向量）"""
        doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="文档不存在")

        # 删除向量
        delete_by_document_id(doc_id)

        # 删除文件
        if doc.file_path and os.path.exists(doc.file_path):
            try:
                os.remove(doc.file_path)
            except OSError:
                pass

        # 删除数据库记录（级联删除chunks）
        db.delete(doc)
        db.commit()
        return True

    @staticmethod
    def get_all_chunks(db: Session) -> List[dict]:
        """获取所有chunk（用于BM25检索）"""
        chunks = db.query(KnowledgeChunk).all()
        return [
            {
                "id": c.id,
                "document_id": c.document_id,
                "content": c.content,
                "chunk_index": c.chunk_index,
            }
            for c in chunks
        ]

    @staticmethod
    def get_stats(db: Session) -> dict:
        """获取知识库统计"""
        total_docs = db.query(KnowledgeDocument).count()
        indexed_docs = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.status == "indexed"
        ).count()
        total_chunks = db.query(KnowledgeChunk).count()

        return {
            "total_documents": total_docs,
            "indexed_documents": indexed_docs,
            "total_chunks": total_chunks,
        }
