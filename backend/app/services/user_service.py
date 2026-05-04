"""
user_service 模块。

在后端项目中的作用：
1. 封装用户管理（查询、创建、编辑、状态变更）与自助资料修改的业务逻辑。
2. 供 API 层调用，避免将权限校验与数据库细节散落在路由层。

优化建议：
- 增加手机号、邮箱唯一性校验。
- 引入操作审计日志，记录管理员对用户的变更历史。
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models import User


def user_to_dict(user: User) -> Dict[str, Any]:
    """将 ORM 用户对象转为可对外返回的字典（不含密码）。"""
    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "real_name": user.real_name,
        "phone": user.phone,
        "email": user.email,
        "status": user.status,
        "created_at": user.created_at.isoformat(),
        "updated_at": user.updated_at.isoformat(),
    }


def _validate_password(password: str) -> Optional[str]:
    """校验密码强度，不合法时返回错误信息。"""
    if not password or len(password) < 8:
        return "密码长度至少 8 位"
    return None


def list_users(
    page: int = 1,
    per_page: int = 20,
    keyword: str = "",
    role: str = "",
    status: Optional[int] = None,
) -> Dict[str, Any]:
    """
    分页查询用户列表（管理员专用）。

    Args:
        page: 页码（从 1 开始）
        per_page: 每页数量
        keyword: 模糊匹配用户名或真实姓名
        role: 精确匹配角色（ADMIN / USER），空字符串表示不过滤
        status: 1=启用 / 0=禁用，None 表示不过滤

    Returns:
        含 items、total、page、per_page 的字典。
    """
    q = User.query
    if keyword:
        like = f"%{keyword}%"
        q = q.filter(
            db.or_(User.username.like(like), User.real_name.like(like))
        )
    if role in ("ADMIN", "USER"):
        q = q.filter(User.role == role)
    if status in (0, 1):
        q = q.filter(User.status == status)
    total = q.count()
    items = (
        q.order_by(User.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return {
        "items": [user_to_dict(u) for u in items],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


def get_user(user_id: int) -> Optional[User]:
    """按主键查询用户。"""
    return db.session.get(User, user_id)


def create_user(data: Dict[str, Any]) -> Tuple[Optional[User], Optional[str]]:
    """
    管理员创建用户。

    Args:
        data: 含 username、password 等字段的字典；role 默认 USER

    Returns:
        (user, None) 成功；(None, error_message) 失败。
    """
    username = (data.get("username") or "").strip()
    if not username or len(username) < 3 or len(username) > 64:
        return None, "用户名长度应为 3～64"
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        return None, "用户名仅允许字母、数字与下划线"
    if User.query.filter_by(username=username).first():
        return None, "用户名已存在"

    password = data.get("password") or ""
    err = _validate_password(password)
    if err:
        return None, err

    role = data.get("role") or "USER"
    if role not in ("ADMIN", "USER"):
        return None, "角色必须是 ADMIN 或 USER"

    user = User(
        username=username,
        password_hash=generate_password_hash(password),
        role=role,
        real_name=(data.get("real_name") or "").strip() or None,
        phone=(data.get("phone") or "").strip() or None,
        email=(data.get("email") or "").strip() or None,
        status=1,
    )
    db.session.add(user)
    db.session.commit()
    return user, None


def update_user(
    user_id: int, data: Dict[str, Any], operator_id: int
) -> Tuple[Optional[User], Optional[str]]:
    """
    管理员编辑用户信息（支持修改角色与重置密码）。

    Args:
        user_id: 被编辑用户的主键
        data: 可含 real_name、phone、email、role、password 字段
        operator_id: 当前操作管理员的 user_id（防止自改角色）

    Returns:
        (user, None) 成功；(None, error_message) 失败。
    """
    user = db.session.get(User, user_id)
    if not user:
        return None, "用户不存在"

    if "role" in data:
        if user_id == operator_id:
            return None, "不能修改自己的角色"
        role = data["role"]
        if role not in ("ADMIN", "USER"):
            return None, "角色必须是 ADMIN 或 USER"
        user.role = role

    for field in ("real_name", "phone", "email"):
        if field in data:
            setattr(user, field, (data[field] or "").strip() or None)

    if "password" in data and data["password"]:
        err = _validate_password(data["password"])
        if err:
            return None, err
        user.password_hash = generate_password_hash(data["password"])

    db.session.commit()
    return user, None


def toggle_user_status(
    user_id: int, new_status: int, operator_id: int
) -> Optional[str]:
    """
    启用或禁用用户账号。

    Args:
        user_id: 目标用户主键
        new_status: 1=启用 / 0=禁用
        operator_id: 当前操作管理员的 user_id（防止自禁）

    Returns:
        None 成功；错误信息字符串 失败。
    """
    if new_status not in (0, 1):
        return "status 必须是 0 或 1"
    if user_id == operator_id:
        return "不能修改自己的账号状态"
    user = db.session.get(User, user_id)
    if not user:
        return "用户不存在"
    user.status = new_status
    db.session.commit()
    return None


def update_own_profile(
    user_id: int, data: Dict[str, Any]
) -> Tuple[Optional[User], Optional[str]]:
    """
    用户自助更新个人资料（real_name、phone、email）。

    Args:
        user_id: 当前登录用户的主键
        data: 含可更新字段的字典

    Returns:
        (user, None) 成功；(None, error_message) 失败。
    """
    user = db.session.get(User, user_id)
    if not user:
        return None, "用户不存在"
    for field in ("real_name", "phone", "email"):
        if field in data:
            setattr(user, field, (data[field] or "").strip() or None)
    db.session.commit()
    return user, None


def change_own_password(
    user_id: int, old_password: str, new_password: str
) -> Optional[str]:
    """
    用户自助修改密码，需要验证旧密码。

    Args:
        user_id: 当前登录用户的主键
        old_password: 旧密码明文
        new_password: 新密码明文

    Returns:
        None 成功；错误信息字符串 失败。
    """
    user = db.session.get(User, user_id)
    if not user:
        return "用户不存在"
    if not check_password_hash(user.password_hash, old_password):
        return "旧密码不正确"
    err = _validate_password(new_password)
    if err:
        return err
    if old_password == new_password:
        return "新密码不能与旧密码相同"
    user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    return None
