"""
认证领域服务模块。

在后端项目中的作用：
1. 封装注册、登录校验、用户公开信息组装等业务逻辑。
2. 避免将数据库与密码细节散落在路由层。

可扩展建议：
- 接入邮箱/手机验证码、登录失败锁定、OAuth2。
- 使用 Marshmallow 或 Pydantic 做请求体验证与错误信息统一。
"""

import re
from typing import Any, Dict, Optional, Tuple

from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models import User


def _validate_username(username: str) -> Optional[str]:
    """校验用户名格式，不合法时返回错误信息。"""
    if not username or len(username) < 3 or len(username) > 64:
        return "用户名长度应为 3～64"
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        return "用户名仅允许字母、数字与下划线"
    return None


def _validate_password(password: str) -> Optional[str]:
    """校验密码强度，不合法时返回错误信息。"""
    if not password or len(password) < 8:
        return "密码长度至少 8 位"
    return None


def user_to_public(user: User) -> Dict[str, Any]:
    """将 ORM 用户转为可对外返回的字典（不含密码）。"""
    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "real_name": user.real_name,
        "phone": user.phone,
        "email": user.email,
        "status": user.status,
    }


def register_user(
    username: str,
    password: str,
    *,
    real_name: Optional[str] = None,
    phone: Optional[str] = None,
    email: Optional[str] = None,
) -> Tuple[Optional[User], Optional[str], Optional[str]]:
    """
    注册新用户（默认角色为 USER）。

    Returns:
        (user, None, None) 表示成功；
        (None, error_message, error_code) 表示失败，error_code 为业务错误码字符串。
    """
    err = _validate_username(username)
    if err:
        return None, err, "40001"
    err = _validate_password(password)
    if err:
        return None, err, "40001"

    if User.query.filter_by(username=username).first():
        return None, "用户名已存在", "40901"

    user = User(
        username=username,
        password_hash=generate_password_hash(password),
        role="USER",
        real_name=real_name,
        phone=phone,
        email=email,
        status=1,
    )
    db.session.add(user)
    db.session.commit()
    return user, None, None


def authenticate_user(username: str, password: str) -> Tuple[Optional[User], Optional[str], Optional[str]]:
    """
    校验用户名与密码。

    Returns:
        (user, None, None) 成功；
        (None, message, code) 失败。
    """
    err = _validate_username(username)
    if err:
        return None, "用户名或密码错误", "40101"
    err = _validate_password(password)
    if err:
        return None, "用户名或密码错误", "40101"

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return None, "用户名或密码错误", "40101"
    if user.status != 1:
        return None, "账号已禁用", "40301"
    return user, None, None


def get_user_by_id(user_id: int) -> Optional[User]:
    """按主键查询用户。"""
    return db.session.get(User, user_id)
