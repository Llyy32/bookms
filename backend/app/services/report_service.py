"""
report_service 模块。

在后端项目中的作用：
1. 封装借阅排行榜、逾期统计、库存统计、用户活跃度四类聚合查询逻辑。
2. 供 reports API 层调用，将统计 SQL 与路由层解耦。

优化建议：
- 对高频调用的聚合查询增加 Redis 缓存层，设置 5~10 分钟 TTL。
- 时间范围参数可扩展为支持按月/季/年的预设快捷选项。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import func

from app.extensions import db
from app.models.book import Book
from app.models.borrow_record import BorrowRecord
from app.models.user import User


def _parse_date_range(
    start_str: Optional[str], end_str: Optional[str]
) -> tuple[Optional[datetime], Optional[datetime]]:
    """
    将日期字符串解析为 datetime 对象，格式要求 YYYY-MM-DD。

    Returns:
        (start_dt, end_dt)，解析失败时对应项返回 None。
    """
    start_dt: Optional[datetime] = None
    end_dt: Optional[datetime] = None
    try:
        if start_str:
            start_dt = datetime.strptime(start_str.strip(), "%Y-%m-%d")
    except ValueError:
        pass
    try:
        if end_str:
            # end 取当天 23:59:59，保证当天数据包含在内
            end_dt = datetime.strptime(end_str.strip(), "%Y-%m-%d").replace(
                hour=23, minute=59, second=59
            )
    except ValueError:
        pass
    return start_dt, end_dt


def get_borrow_ranking(
    limit: int = 20,
    start_str: Optional[str] = None,
    end_str: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    借阅排行榜：按图书被借阅次数降序，含书名、作者、分类。

    Args:
        limit: 返回条数上限
        start_str: 借阅时间起始日期（YYYY-MM-DD），None 表示不限
        end_str: 借阅时间截止日期（YYYY-MM-DD），None 表示不限

    Returns:
        列表，每项含 book_id、title、author、category、borrow_count。
    """
    start_dt, end_dt = _parse_date_range(start_str, end_str)

    q = (
        db.session.query(
            BorrowRecord.book_id,
            func.count(BorrowRecord.id).label("borrow_count"),
        )
        .group_by(BorrowRecord.book_id)
    )
    if start_dt:
        q = q.filter(BorrowRecord.borrowed_at >= start_dt)
    if end_dt:
        q = q.filter(BorrowRecord.borrowed_at <= end_dt)
    q = q.order_by(func.count(BorrowRecord.id).desc()).limit(limit)

    rows = q.all()
    result = []
    for row in rows:
        book = db.session.get(Book, row.book_id)
        result.append(
            {
                "book_id": row.book_id,
                "title": book.title if book else "（已删除）",
                "author": book.author if book else "-",
                "category": book.category if book else "-",
                "borrow_count": row.borrow_count,
            }
        )
    return result


def get_overdue_summary(
    start_str: Optional[str] = None,
    end_str: Optional[str] = None,
) -> Dict[str, Any]:
    """
    逾期统计：总逾期记录数、当前仍逾期数、已归还的历史逾期数。

    Args:
        start_str: 借阅时间起始日期，None 表示不限
        end_str: 借阅时间截止日期，None 表示不限

    Returns:
        含 total_overdue、currently_overdue、returned_overdue、top_books 的字典。
        top_books 为逾期次数最多的前 10 本书。
    """
    start_dt, end_dt = _parse_date_range(start_str, end_str)

    base_q = BorrowRecord.query.filter(
        BorrowRecord.status.in_(["OVERDUE", "RETURNED"]),
        BorrowRecord.due_at < func.now(),
    )
    if start_dt:
        base_q = base_q.filter(BorrowRecord.borrowed_at >= start_dt)
    if end_dt:
        base_q = base_q.filter(BorrowRecord.borrowed_at <= end_dt)

    total_overdue = base_q.count()
    currently_overdue = base_q.filter(BorrowRecord.status == "OVERDUE").count()
    returned_overdue = total_overdue - currently_overdue

    # 逾期次数最多的前 10 本书
    top_q = (
        db.session.query(
            BorrowRecord.book_id,
            func.count(BorrowRecord.id).label("overdue_count"),
        )
        .filter(
            BorrowRecord.status.in_(["OVERDUE", "RETURNED"]),
            BorrowRecord.due_at < func.now(),
        )
        .group_by(BorrowRecord.book_id)
        .order_by(func.count(BorrowRecord.id).desc())
        .limit(10)
    )
    if start_dt:
        top_q = top_q.filter(BorrowRecord.borrowed_at >= start_dt)
    if end_dt:
        top_q = top_q.filter(BorrowRecord.borrowed_at <= end_dt)

    top_books = []
    for row in top_q.all():
        book = db.session.get(Book, row.book_id)
        top_books.append(
            {
                "book_id": row.book_id,
                "title": book.title if book else "（已删除）",
                "overdue_count": row.overdue_count,
            }
        )

    return {
        "total_overdue": total_overdue,
        "currently_overdue": currently_overdue,
        "returned_overdue": returned_overdue,
        "top_books": top_books,
    }


def get_stock_summary() -> Dict[str, Any]:
    """
    库存统计：全库总册数、可借册数、在借册数，以及各分类汇总。

    Returns:
        含 total_stock、available_stock、borrowed_stock、by_category 的字典。
    """
    # 仅统计在架图书（status=1）
    totals = db.session.query(
        func.sum(Book.total_stock).label("total"),
        func.sum(Book.available_stock).label("available"),
    ).filter(Book.status == 1).first()

    total_stock = int(totals.total or 0)
    available_stock = int(totals.available or 0)
    borrowed_stock = total_stock - available_stock

    # 按分类聚合
    by_category_rows = (
        db.session.query(
            Book.category,
            func.sum(Book.total_stock).label("total"),
            func.sum(Book.available_stock).label("available"),
        )
        .filter(Book.status == 1)
        .group_by(Book.category)
        .all()
    )
    by_category = [
        {
            "category": row.category or "未分类",
            "total_stock": int(row.total or 0),
            "available_stock": int(row.available or 0),
            "borrowed_stock": int(row.total or 0) - int(row.available or 0),
        }
        for row in by_category_rows
    ]

    return {
        "total_stock": total_stock,
        "available_stock": available_stock,
        "borrowed_stock": borrowed_stock,
        "by_category": by_category,
    }


def get_user_activity(
    limit: int = 20,
    start_str: Optional[str] = None,
    end_str: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    用户活跃度：按借阅次数降序排列的用户列表。

    Args:
        limit: 返回条数上限
        start_str: 借阅时间起始日期，None 表示不限
        end_str: 借阅时间截止日期，None 表示不限

    Returns:
        列表，每项含 user_id、username、real_name、borrow_count。
    """
    start_dt, end_dt = _parse_date_range(start_str, end_str)

    q = (
        db.session.query(
            BorrowRecord.user_id,
            func.count(BorrowRecord.id).label("borrow_count"),
        )
        .group_by(BorrowRecord.user_id)
    )
    if start_dt:
        q = q.filter(BorrowRecord.borrowed_at >= start_dt)
    if end_dt:
        q = q.filter(BorrowRecord.borrowed_at <= end_dt)
    q = q.order_by(func.count(BorrowRecord.id).desc()).limit(limit)

    rows = q.all()
    result = []
    for row in rows:
        user = db.session.get(User, row.user_id)
        result.append(
            {
                "user_id": row.user_id,
                "username": user.username if user else "（已删除）",
                "real_name": user.real_name if user else None,
                "borrow_count": row.borrow_count,
            }
        )
    return result
