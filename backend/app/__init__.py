"""
应用工厂模块。

在后端项目中的作用：
1. 统一创建 Flask 应用实例并加载配置。
2. 初始化扩展与路由，是后端启动的核心装配点。

可扩展建议：
- 在这里集中注册中间件、错误处理器、日志系统。
- 增加按环境加载不同配置类的能力。
"""

from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

from config import Config
from .api import register_blueprints
from .extensions import db, migrate


def create_app() -> Flask:
    """创建并返回 Flask 应用实例。"""
    load_dotenv()
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(
        app,
        supports_credentials=True,
        origins=app.config.get("CORS_ORIGINS", []),
        allow_headers=["Content-Type", "Authorization"],
        expose_headers=["Content-Type"],
    )

    # 初始化数据库与迁移扩展，确保模型可被迁移工具识别
    db.init_app(app)
    migrate.init_app(app, db)
    # 统一注册 API 蓝图，所有接口都挂载在 /api/v1 下
    register_blueprints(app)

    return app
