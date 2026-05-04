"""
reservation_service 模块。

在后端项目中的作用：
1. 封装预约创建、取消、到期懒标记、借阅自动履行等业务规则。
2. 供 API 层和 borrow_service 调用，保证预约与借阅状态联动一致。

优化建议：
- 预约到期时间可改为系统配置项，避免硬编码。
- 履行逻辑可扩展为通知用户（邮件/短信）。
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

from app.extensions import db
from app.models.book import Book
from app.models.reservation import Reservation
from app.models.user import User

RESERVATION_EXPIRE_DAYS = 3


def reservation_to_dict(r: Reservation) -> Dict[str, Any]:
    """将预约 ORM 对象转为可对外返回的字典，附带图书与用户基本信息。"""
    book = db.session.get(Book, r.book_id)
    user = db.session.get(User, r.user_id)
    return {
        "id": r.id,
        "user_id": r.user_id,
        "username": user.username if user else None,
        "book_id": r.book_id,
        "book_title": book.title if book else None,
        "book_author": book.author if book else None,
        "status": r.status,
        "reserved_at": r.reserved_at.isoformat(),
        "expired_at": r.expired_at.isoformat() if r.expired_at else None,
        "created_at": r.created_at.isoformat(),
        "updated_at": r.updated_at.isoformat(),
    }


def _refresh_expired_all() -> None:
    """将全库已超期但状态仍为 ACTIVE 的预约记录批量标记为 EXPIRED（懒触发）。"""
    Reservation.query.filter(
        Reservation.status == "ACTIVE",
        Reservation.expired_at < datetime.utcnow(),
    ).update({"status": "EXPIRED"}, synchronize_session=False)
    db.session.commit()


def fulfill_reservation_for_borrow(user_id: int, book_id: int) -> None:
    """
    借阅成功后，将该用户对该书的 ACTIVE 预约自动标记为 FULFILLED。

    Args:
        user_id: 借阅用户主键
        book_id: 借阅图书主键
    """
    reservation = Reservation.query.filter_by(
        user_id=user_id,
        book_id=book_id,
        status="ACTIVE",
    ).first()
    if reservation:
        reservation.status = "FULFILLED"
        db.session.commit()


def create_reservation(
    user_id: int, book_id: int
) -> Tuple[Optional[Reservation], Optional[str]]:
    """
    创建预约（有库存也允许预约）。

    校验：图书存在且在架；该用户对该书没有进行中的 ACTIVE 预约。

    Args:
        user_id: 预约用户主键
        book_id: 待预约图书主键

    Returns:
        (reservation, None) 成功；(None, error_message) 失败。
    """
    book = db.session.get(Book, book_id)
    if not book:
        return None, "图书不存在"
    if book.status != 1:
        return None, "该图书已下架，无法预约"

    existing = Reservation.query.filter_by(
        user_id=user_id,
        book_id=book_id,
        status="ACTIVE",
    ).first()
    if existing:
        return None, "您已对该书有进行中的预约"

    now = datetime.utcnow()
    reservation = Reservation(
        user_id=user_id,
        book_id=book_id,
        status="ACTIVE",
        reserved_at=now,
        expired_at=now + timedelta(days=RESERVATION_EXPIRE_DAYS),
    )
    db.session.add(reservation)
    db.session.commit()
    return reservation, None


def cancel_reservation(
    reservation_id: int, operator_user_id: int, is_admin: bool
) -> Tuple[Optional[Reservation], Optional[str]]:
    """
    取消预约，仅限 ACTIVE 状态，本人或管理员可操作。

    Args:
        reservation_id: 预约记录主键
        operator_user_id: 操作人 user_id
        is_admin: 是否为管理员

    Returns:
        (reservation, None) 成功；(None, error_message) 失败。
    """
    reservation = db.session.get(Reservation, reservation_id)
    if not reservation:
        return None, "预约记录不存在"
    if not is_admin and reservation.user_id != operator_user_id:
        return None, "无权操作此预约"
    if reservation.status != "ACTIVE":
        return None, f"预约当前状态为 {reservation.status}，无法取消"

    reservation.status = "CANCELLED"
    db.session.commit()
    return reservation, None


def list_reservations(
    page: int = 1,
    per_page: int = 20,
    user_id: Optional[int] = None,
    status: str = "",
    book_keyword: str = "",
) -> Dict[str, Any]:
    """
    分页查询预约记录，查询前触发全库到期懒更新。

    Args:
        page: 页码（从 1 开始）
        per_page: 每页数量
        user_id: 过滤指定用户（None 表示查全部，管理员专用）
        status: 过滤状态（ACTIVE / CANCELLED / FULFILLED / EXPIRED），空表示全部
        book_keyword: 按书名或作者模糊搜索

    Returns:
        含 items、total、page、per_page 的字典。
    """
    _refresh_expired_all()

    q = Reservation.query
    if user_id is not None:
        q = q.filter(Reservation.user_id == user_id)
    if status in ("ACTIVE", "CANCELLED", "FULFILLED", "EXPIRED"):
        q = q.filter(Reservation.status == status)
    if book_keyword:
        like = f"%{book_keyword}%"
        q = q.join(Book, Reservation.book_id == Book.id).filter(
            db.or_(Book.title.like(like), Book.author.like(like))
        )

    total = q.count()
    items = (
        q.order_by(Reservation.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return {
        "items": [reservation_to_dict(r) for r in items],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


def get_reservation(reservation_id: int) -> Optional[Reservation]:
    """按主键查询预约记录。"""
    return db.session.get(Reservation, reservation_id)
