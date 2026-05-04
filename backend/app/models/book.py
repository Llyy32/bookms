"""
图书模型模块。

在后端项目中的作用：
1. 定义图书信息与库存字段结构。
2. 为图书管理、借阅和报表统计提供基础数据实体。

可扩展建议：
- 增加封面 URL、摘要、馆藏位置等业务字段。
- 增加库存变更日志关联。
"""

from datetime import datetime

from app.extensions import db


class Book(db.Model):
    """图书 ORM 模型。"""

    __tablename__ = "books"

    id = db.Column(db.BigInteger, primary_key=True)
    isbn = db.Column(db.String(32), unique=True)
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(128), nullable=False)
    category = db.Column(db.String(64))
    publisher = db.Column(db.String(128))
    publish_date = db.Column(db.Date)
    total_stock = db.Column(db.Integer, nullable=False, default=0)
    available_stock = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.SmallInteger, nullable=False, default=1)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
