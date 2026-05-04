"""
预约记录模型模块。

在后端项目中的作用：
1. 定义预约业务数据结构与状态字段。
2. 关联用户与图书，支持预约流程管理。

可扩展建议：
- 增加取书截止时间与通知状态字段。
- 增加预约队列顺序与优先级管理字段。
"""

from datetime import datetime

from app.extensions import db


class Reservation(db.Model):
    """预约记录 ORM 模型。"""

    __tablename__ = "reservations"

    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=False)
    book_id = db.Column(db.BigInteger, db.ForeignKey("books.id"), nullable=False)
    status = db.Column(
        db.Enum("ACTIVE", "CANCELLED", "FULFILLED", "EXPIRED"),
        nullable=False,
        default="ACTIVE",
    )
    reserved_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expired_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
