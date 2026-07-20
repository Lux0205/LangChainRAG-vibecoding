"""知识库管理API路由（管理员专用）"""
from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.middleware.auth_middleware import get_current_admin
from app.models.user import User
from app.services.knowledge_service import KnowledgeService
from app.schemas.auth import MessageResponse

router = APIRouter(prefix="/knowledge", tags=["知识库管理"])


@router.post("/upload", response_model=MessageResponse, summary="上传知识文档")
async def upload_document(
    file: UploadFile = File(..., description="知识文档文件"),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """上传知识文档（PDF/DOCX/TXT/CSV），自动索引到向量库"""
    doc = await KnowledgeService.upload_document(db, file, current_admin)
    return MessageResponse(
        message=f"文档《{doc.title}》上传成功，已索引 {doc.chunk_count} 个片段"
    )


@router.get("/documents", summary="获取文档列表")
async def get_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = Query(None),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """获取知识库文档列表（分页）"""
    return KnowledgeService.get_documents(db, page, page_size, keyword)


@router.delete("/documents/{doc_id}", response_model=MessageResponse, summary="删除文档")
async def delete_document(
    doc_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """删除知识文档（同步删除向量索引）"""
    KnowledgeService.delete_document(db, doc_id)
    return MessageResponse(message="文档删除成功")


@router.get("/stats", summary="知识库统计")
async def get_stats(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """获取知识库统计信息"""
    return KnowledgeService.get_stats(db)
