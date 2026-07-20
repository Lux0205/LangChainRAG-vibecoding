"""问答与聊天API路由"""
import json
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.services.chat_service import ChatService
from app.schemas.auth import MessageResponse

router = APIRouter(prefix="/chat", tags=["问答聊天"])


@router.post("/sessions", summary="创建新会话")
async def create_session(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建新的聊天会话"""
    session = ChatService.create_session(db, current_user.id)
    return session.to_dict()


@router.get("/sessions", summary="获取会话列表")
async def get_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的所有会话"""
    sessions = ChatService.get_user_sessions(db, current_user.id)
    return [s.to_dict() for s in sessions]


@router.delete("/sessions/{session_id}", response_model=MessageResponse, summary="删除会话")
async def delete_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除指定会话"""
    success = ChatService.delete_session(db, session_id, current_user.id)
    if not success:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="会话不存在")
    return MessageResponse(message="会话删除成功")


@router.get("/sessions/{session_id}/messages", summary="获取会话消息")
async def get_messages(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取指定会话的所有消息"""
    messages = ChatService.get_messages(db, session_id, current_user.id)
    return [m.to_dict() for m in messages]


@router.post("/chat", summary="发送消息（流式）")
async def chat(
    session_id: int,
    question: str,
    provider: Optional[str] = Query(None, description="LLM提供商: tongyi/zhipu"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    发送消息并流式返回回答
    使用SSE协议，返回格式:
    - {"type": "token", "content": "文本"}  - 逐字输出
    - {"type": "citations", "data": [...]}  - 引用来源
    - {"type": "done"}                     - 完成
    """
    async def event_generator():
        async for chunk in ChatService.chat_stream(
            db=db,
            session_id=session_id,
            user_id=current_user.id,
            question=question,
            provider=provider,
        ):
            yield f"data: {chunk}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
