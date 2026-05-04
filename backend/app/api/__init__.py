"""
API 蓝图注册模块。

在后端项目中的作用：
1. 集中管理所有业务蓝图，统一挂载到 /api/v1 路径体系。
2. 让 app 初始化逻辑保持简洁，避免在工厂函数中散落注册代码。

可扩展建议：
- 增加版本化管理（如 /api/v2）。
- 增加按环境动态启用调试蓝图。
"""

from flask import Flask

from .auth import bp as auth_bp
from .books import bp as books_bp
from .borrow_records import bp as borrow_bp
from .health import bp as health_bp
from .reports import bp as reports_bp
from .reservations import bp as reservations_bp
from .users import bp as users_bp


def register_blueprints(app: Flask) -> None:
    """向应用注册全部 API 蓝图。"""
    app.register_blueprint(health_bp, url_prefix="/api/v1")
    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(users_bp, url_prefix="/api/v1/users")
    app.register_blueprint(books_bp, url_prefix="/api/v1/books")
    app.register_blueprint(borrow_bp, url_prefix="/api/v1/borrow-records")
    app.register_blueprint(reservations_bp, url_prefix="/api/v1/reservations")
    app.register_blueprint(reports_bp, url_prefix="/api/v1/reports")
