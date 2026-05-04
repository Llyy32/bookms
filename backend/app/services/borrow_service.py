"""
borrow_service 模块。

在后端项目中的作用：
1. 封装借阅、归还、逾期懒标记等核心业务规则，供 API 层调用。
2. 保证库存变更与记录写入在同一事务内，防止数据不一致。

优化建议：
- 借阅与库存扣减可改为 SELECT FOR UPDATE 悲观锁，防高并发超借。
- 逾期懒更新可拆分为后台定时任务，降低查询时的写压力。
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from app.extensions import db
from app.models.book import Book
from app.models.borrow_record import BorrowRecord
from app.models.user import User
from app.services.reservation_service import fulfill_reservation_for_borrow

MAX_BORROW_COUNT = 5
BORROW_DAYS = 30


def borrow_to_dict(record: BorrowRecord) -> Dict[str, Any]:
    """
    将借阅记录 ORM 对象转为可对外返回的字典，附带图书与用户基本信息。

    Returns:
        含借阅记录字段及 book_title、book_author、username 的字典。
    """
    book = db.session.get(Book, record.book_id)
    user = db.session.get(User, record.user_id)
    return {
        "id": record.id,
        "user_id": record.user_id,
        "username": user.username if user else None,
        "book_id": record.book_id,
        "book_title": book.title if book else None,
        "book_author": book.author if book else None,
        "borrowed_at": record.borrowed_at.isoformat(),
        "due_at": record.due_at.isoformat(),
        "returned_at": record.returned_at.isoformat() if record.returned_at else None,
        "status": record.status,
        "created_at": record.created_at.isoformat(),
        "updated_at": record.updated_at.isoformat(),
    }


def _refresh_overdue_for_user(user_id: int) -> None:
    """将指定用户已超期但状态仍为 BORROWED 的记录批量标记为 OVERDUE。"""
    BorrowRecord.query.filter(
        BorrowRecord.user_id == user_id,
        BorrowRecord.status == "BORROWED",
        BorrowRecord.due_at < datetime.utcnow(),
    ).update({"status": "OVERDUE"}, synchronize_session=False)
    db.session.commit()


def _refresh_overdue_all() -> None:
    """将全库已超期但状态仍为 BORROWED 的记录批量标记为 OVERDUE（查询时懒触发）。"""
    BorrowRecord.query.filter(
        BorrowRecord.status == "BORROWED",
        BorrowRecord.due_at < datetime.utcnow(),
    ).update({"status": "OVERDUE"}, synchronize_session=False)
    db.session.commit()


def create_borrow(
    user_id: int, book_id: int
) -> Tuple[Optional[BorrowRecord], Optional[str]]:
    """
    创建借阅记录，含完整业务规则校验。

    校验顺序：逾期限制 → 借阅上限 → 图书状态/库存 → 是否已借此书未还。

    Args:
        user_id: 借阅用户的主键
        book_id: 待借图书的主键

    Returns:
        (record, None) 成功；(None, error_message) 失败。
    """
    # 先将该用户的超期记录懒标记为 OVERDUE
    _refresh_overdue_for_user(user_id)

    # 规则1：有逾期未还时禁止借阅
    overdue_count = BorrowRecord.query.filter_by(
        user_id=user_id, status="OVERDUE"
    ).count()
    if overdue_count > 0:
        return None, f"您有 {overdue_count} 本逾期未还，请先归还后再借阅"

    # 规则2：在借数量不得超过上限
    active_count = BorrowRecord.query.filter_by(
        user_id=user_id, status="BORROWED"
    ).count()
    if active_count >= MAX_BORROW_COUNT:
        return None, f"已达最大借阅上限（{MAX_BORROW_COUNT} 册）"

    # 规则3：图书必须在架且有库存
    book = db.session.get(Book, book_id)
    if not book:
        return None, "图书不存在"
    if book.status != 1:
        return None, "该图书已下架，无法借阅"
    if book.available_stock <= 0:
        return None, "该图书暂无可借副本，库存不足"

    # 规则4：同一本书不能重复借阅（上一本未还）
    duplicate = BorrowRecord.query.filter(
        BorrowRecord.user_id == user_id,
        BorrowRecord.book_id == book_id,
        BorrowRecord.status.in_(["BORROWED", "OVERDUE"]),
    ).first()
    if duplicate:
        return None, "您已借阅此书且尚未归还"

    now = datetime.utcnow()
    record = BorrowRecord(
        user_id=user_id,
        book_id=book_id,
        borrowed_at=now,
        due_at=now + timedelta(days=BORROW_DAYS),
        status="BORROWED",
    )
    book.available_stock -= 1
    db.session.add(record)
    db.session.commit()

    # 借阅成功后自动履行该用户对此书的进行中预约
    fulfill_reservation_for_borrow(user_id, book_id)

    return record, None


def return_borrow(
    record_id: int, operator_user_id: int, is_admin: bool
) -> Tuple[Optional[BorrowRecord], Optional[str]]:
    """
    归还图书，可用库存原子加 1。

    Args:
        record_id: 借阅记录主键
        operator_user_id: 操作人 user_id（用于权限校验）
        is_admin: 是否为管理员（管理员可归还任意记录）

    Returns:
        (record, None) 成功；(None, error_message) 失败。
    """
    record = db.session.get(BorrowRecord, record_id)
    if not record:
        return None, "借阅记录不存在"
    if not is_admin and record.user_id != operator_user_id:
        return None, "无权操作此借阅记录"
    if record.status == "RETURNED":
        return None, "该书已归还"

    record.returned_at = datetime.utcnow()
    record.status = "RETURNED"

    book = db.session.get(Book, record.book_id)
    if book:
        book.available_stock += 1

    db.session.commit()
    return record, None


def list_borrows(
    page: int = 1,
    per_page: int = 20,
    user_id: Optional[int] = None,
    status: str = "",
    book_keyword: str = "",
) -> Dict[str, Any]:
    """
    分页查询借阅记录，查询前触发全库逾期懒更新。

    Args:
        page: 页码（从 1 开始）
        per_page: 每页数量
        user_id: 过滤指定用户（None 表示查全部，管理员专用）
        status: 过滤状态（BORROWED / OVERDUE / RETURNED），空字符串表示全部
        book_keyword: 按书名或作者模糊搜索

    Returns:
        含 items、total、page、per_page 的字典。
    """
    _refresh_overdue_all()

    q = BorrowRecord.query
    if user_id is not None:
        q = q.filter(BorrowRecord.user_id == user_id)
    if status in ("BORROWED", "OVERDUE", "RETURNED"):
        q = q.filter(BorrowRecord.status == status)
    if book_keyword:
        like = f"%{book_keyword}%"
        q = q.join(Book, BorrowRecord.book_id == Book.id).filter(
            db.or_(Book.title.like(like), Book.author.like(like))
        )

    total = q.count()
    records = (
        q.order_by(BorrowRecord.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return {
        "items": [borrow_to_dict(r) for r in records],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


def get_borrow(record_id: int) -> Optional[BorrowRecord]:
    """按主键查询借阅记录。"""
    return db.session.get(BorrowRecord, record_id)
