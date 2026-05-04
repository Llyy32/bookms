"""
用户模型模块。

在后端项目中的作用：
1. 定义用户数据结构（管理员与普通用户）。
2. 为认证、权限与用户管理提供基础实体。

可扩展建议：
- 增加最后登录时间、密码更新时间等安全字段。
- 增加软删除标记与审计字段。
"""

from datetime import datetime

from app.extensions import db


class User(db.Model):
    """用户 ORM 模型。"""

    __tablename__ = "users"

    id = db.Column(db.BigInteger, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum("ADMIN", "USER"), nullable=False, default="USER")
    real_name = db.Column(db.String(64))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(128))
    status = db.Column(db.SmallInteger, nullable=False, default=1)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
