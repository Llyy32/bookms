"""
借阅记录模型模块。

在后端项目中的作用：
1. 定义借阅状态流转相关数据结构。
2. 关联用户与图书，承载借阅生命周期信息。

可扩展建议：
- 增加续借次数、操作来源、处理人等字段。
- 增加索引以优化高频查询场景。
"""

from datetime import datetime

from app.extensions import db


class BorrowRecord(db.Model):
    """借阅记录 ORM 模型。"""

    __tablename__ = "borrow_records"

    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=False)
    book_id = db.Column(db.BigInteger, db.ForeignKey("books.id"), nullable=False)
    borrowed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    due_at = db.Column(db.DateTime, nullable=False)
    returned_at = db.Column(db.DateTime)
    status = db.Column(
        db.Enum("BORROWED", "OVERDUE", "RETURNED"), nullable=False, default="BORROWED"
    )
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
