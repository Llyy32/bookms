"""
登录态与角色装饰器模块。

在后端项目中的作用：
1. 保护需要登录或管理员权限的接口。
2. 统一未授权与无权限的响应结构。

可扩展建议：
- 增加细粒度权限点（如 borrow:create）。
- 将当前用户对象挂载到 g 并从数据库刷新，避免会话与库不一致。
"""

from functools import wraps
from typing import Any, Callable, TypeVar, cast

from flask import jsonify, session

F = TypeVar("F", bound=Callable[..., Any])


def login_required(view: F) -> F:
    """要求请求携带有效登录会话（Session 中存在 user_id）。"""

    @wraps(view)
    def wrapped(*args: Any, **kwargs: Any):
        if not session.get("user_id"):
            return (
                jsonify({"code": 40101, "message": "未登录或会话已失效", "data": None}),
                401,
            )
        return view(*args, **kwargs)

    return cast(F, wrapped)


def admin_required(view: F) -> F:
    """要求当前用户角色为管理员。"""

    @wraps(view)
    def wrapped(*args: Any, **kwargs: Any):
        if not session.get("user_id"):
            return (
                jsonify({"code": 40101, "message": "未登录或会话已失效", "data": None}),
                401,
            )
        if session.get("role") != "ADMIN":
            return (
                jsonify({"code": 40301, "message": "需要管理员权限", "data": None}),
                403,
            )
        return view(*args, **kwargs)

    return cast(F, wrapped)
