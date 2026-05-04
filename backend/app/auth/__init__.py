"""
认证相关公共模块包。

在后端项目中的作用：
1. 聚合登录态装饰器、权限校验等横切能力。
2. 与业务 API 解耦，便于在多个蓝图中复用。

可扩展建议：
- 增加 RBAC、接口级权限、审计日志等能力。
"""

from .decorators import admin_required, login_required

__all__ = ["login_required", "admin_required"]
