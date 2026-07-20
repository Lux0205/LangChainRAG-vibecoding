"""管理员API - 用户管理"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.middleware.auth_middleware import get_current_admin
from app.models.user import User
from app.schemas.auth import MessageResponse

router = APIRouter(prefix="/admin", tags=["管理员"])


@router.get("/users", summary="用户列表")
async def get_users(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """获取所有用户列表"""
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [u.to_dict() for u in users]


@router.put("/users/{user_id}/role", response_model=MessageResponse, summary="修改用户角色")
async def update_user_role(
    user_id: int,
    role: str,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """修改用户角色（admin/user）"""
    if role not in ("admin", "user"):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="角色必须是 admin 或 user")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="用户不存在")

    user.role = role
    db.commit()
    return MessageResponse(message=f"用户 {user.username} 角色已修改为 {role}")


@router.delete("/users/{user_id}", response_model=MessageResponse, summary="删除用户")
async def delete_user(
    user_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """删除用户"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="用户不存在")

    if user.id == current_admin.id:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="不能删除自己")

    db.delete(user)
    db.commit()
    return MessageResponse(message=f"用户 {user.username} 已删除")
