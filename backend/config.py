"""
全局配置模块。

在后端项目中的作用：
1. 集中管理 Flask 与数据库配置，降低散落配置带来的维护成本。
2. 通过环境变量解耦本地、测试、生产环境差异。

可扩展建议：
- 拆分 DevelopmentConfig/ProductionConfig/TestConfig。
- 增加 Session 安全配置和日志配置项。
"""

import os
from datetime import timedelta


class Config:
    """基础配置类，供应用工厂读取。"""

    # 秘钥
    SECRET_KEY = os.getenv("SECRET_KEY", "bookms-dev-secret")
    # 禁用SQLAlchemy的修改跟踪
    SQLALCHEMY_TRACK_MODIFICATIONS = False 
    # 调试模式
    DEBUG = os.getenv("DEBUG", False)
    # 数据库配置
    mysql_host = os.getenv("MYSQL_HOST", "localhost")
    mysql_port = os.getenv("MYSQL_PORT", "3306")
    mysql_user = os.getenv("MYSQL_USER", "root")
    mysql_password = os.getenv("MYSQL_PASSWORD", "root")
    mysql_database = os.getenv("MYSQL_DATABASE", "bookms")
    # 数据库URI
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{mysql_user}:{mysql_password}"
        f"@{mysql_host}:{mysql_port}/{mysql_database}?charset=utf8mb4"
    )

    # Session：与前端跨端口联调时保持 Cookie 可用（同站不同端口一般为 Lax）
    SESSION_COOKIE_HTTPONLY = True    # javascript不能访问cookie    
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax") # 同站不同端口一般为 Lax
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() in ("1", "true", "yes") # 是否仅通过 HTTPS 传输 Cookie
    PERMANENT_SESSION_LIFETIME = timedelta(hours=int(os.getenv("SESSION_LIFETIME_HOURS", "168"))) # 会话过期时间7天

    # 允许携带 Cookie 的前端来源，逗号分隔
    CORS_ORIGINS = [
        o.strip()
        for o in os.getenv(
            "CORS_ORIGINS",
            "http://127.0.0.1:5173,http://localhost:5173",
        ).split(",")
        if o.strip()
    ]

