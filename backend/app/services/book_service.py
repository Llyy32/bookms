"""
book_service 模块。

在后端项目中的作用：
1. 封装图书 CRUD、库存调整、软删除等业务逻辑，供 API 层调用。
2. 隔离数据库操作细节，保持路由层简洁，降低层间耦合。

优化建议：
- 库存调整可加悲观锁（SELECT FOR UPDATE）防并发超卖。
- 使用 Marshmallow 或 Pydantic 统一请求体验证与错误格式。
"""

from typing import Any, Dict, Optional, Tuple

from app.extensions import db
from app.models.book import Book


def book_to_dict(book: Book) -> Dict[str, Any]:
    """将 ORM 图书对象转为可对外返回的字典（不含内部字段）。"""
    return {
        "id": book.id,
        "isbn": book.isbn,
        "title": book.title,
        "author": book.author,
        "category": book.category,
        "publisher": book.publisher,
        "publish_date": book.publish_date.isoformat() if book.publish_date else None,
        "total_stock": book.total_stock,
        "available_stock": book.available_stock,
        "status": book.status,
        "created_at": book.created_at.isoformat(),
        "updated_at": book.updated_at.isoformat(),
    }


def list_books(
    page: int = 1,
    per_page: int = 20,
    keyword: str = "",
    category: str = "",
    include_offline: bool = False,
) -> Dict[str, Any]:
    """
    分页查询图书列表。

    Args:
        page: 页码（从 1 开始）
        per_page: 每页数量，最大 100
        keyword: 模糊匹配书名、作者或 ISBN
        category: 精确匹配分类
        include_offline: 是否包含 status=0 的下架图书（管理员专用）

    Returns:
        含 items、total、page、per_page 的字典。
    """
    q = Book.query
    if not include_offline:
        q = q.filter(Book.status == 1)
    if keyword:
        like = f"%{keyword}%"
        q = q.filter(
            db.or_(
                Book.title.like(like),
                Book.author.like(like),
                Book.isbn.like(like),
            )
        )
    if category:
        q = q.filter(Book.category == category)
    total = q.count()
    items = (
        q.order_by(Book.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return {
        "items": [book_to_dict(b) for b in items],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


def get_book(book_id: int) -> Optional[Book]:
    """按主键查询图书（含下架）。"""
    return db.session.get(Book, book_id)


def create_book(data: Dict[str, Any]) -> Tuple[Optional[Book], Optional[str]]:
    """
    新增图书入库。

    Args:
        data: 含 title、author 等字段的字典

    Returns:
        (book, None) 成功；(None, error_message) 失败。
    """
    title = (data.get("title") or "").strip()
    author = (data.get("author") or "").strip()
    if not title:
        return None, "书名不能为空"
    if not author:
        return None, "作者不能为空"

    isbn = (data.get("isbn") or "").strip() or None
    if isbn and Book.query.filter_by(isbn=isbn).first():
        return None, "ISBN 已存在"

    try:
        total_stock = int(data.get("total_stock") or 0)
    except (TypeError, ValueError):
        return None, "总库存必须是整数"
    if total_stock < 0:
        return None, "总库存不能为负"

    book = Book(
        isbn=isbn,
        title=title,
        author=author,
        category=(data.get("category") or "").strip() or None,
        publisher=(data.get("publisher") or "").strip() or None,
        publish_date=data.get("publish_date") or None,
        total_stock=total_stock,
        available_stock=total_stock,
        status=1,
    )
    db.session.add(book)
    db.session.commit()
    return book, None


def update_book(
    book_id: int, data: Dict[str, Any]
) -> Tuple[Optional[Book], Optional[str]]:
    """
    编辑图书基本信息（不含库存调整）。

    Args:
        book_id: 图书主键
        data: 待更新字段字典

    Returns:
        (book, None) 成功；(None, error_message) 失败。
    """
    book = db.session.get(Book, book_id)
    if not book:
        return None, "图书不存在"

    if "title" in data:
        title = (data["title"] or "").strip()
        if not title:
            return None, "书名不能为空"
        book.title = title

    if "author" in data:
        author = (data["author"] or "").strip()
        if not author:
            return None, "作者不能为空"
        book.author = author

    if "isbn" in data:
        isbn = (data["isbn"] or "").strip() or None
        if isbn and isbn != book.isbn:
            if Book.query.filter_by(isbn=isbn).first():
                return None, "ISBN 已存在"
        book.isbn = isbn

    for field in ("category", "publisher"):
        if field in data:
            setattr(book, field, (data[field] or "").strip() or None)

    if "publish_date" in data:
        book.publish_date = data["publish_date"] or None

    db.session.commit()
    return book, None


def delete_book(book_id: int) -> Optional[str]:
    """
    软删除图书（将 status 设为 0 下架）。

    Returns:
        None 成功；错误信息字符串 失败。
    """
    book = db.session.get(Book, book_id)
    if not book:
        return "图书不存在"
    if book.status == 0:
        return "图书已是下架状态"
    book.status = 0
    db.session.commit()
    return None


def restore_book(book_id: int) -> Optional[str]:
    """
    恢复下架图书（将 status 重设为 1 上架）。

    Returns:
        None 成功；错误信息字符串 失败。
    """
    book = db.session.get(Book, book_id)
    if not book:
        return "图书不存在"
    if book.status == 1:
        return "图书已是在架状态"
    book.status = 1
    db.session.commit()
    return None


def adjust_stock(book_id: int, delta: int) -> Tuple[Optional[Book], Optional[str]]:
    """
    调整图书库存，delta 为正增加，为负减少。

    Args:
        book_id: 图书主键
        delta: 库存变化量（可正可负）

    Returns:
        (book, None) 成功；(None, error_message) 失败。
    """
    book = db.session.get(Book, book_id)
    if not book:
        return None, "图书不存在"

    new_total = book.total_stock + delta
    new_available = book.available_stock + delta

    if new_total < 0:
        return None, "调整后总库存不能低于 0"
    if new_available < 0:
        borrowed = book.total_stock - book.available_stock
        return None, f"调整后可用库存为负（当前借出 {borrowed} 册），请先等待归还"

    book.total_stock = new_total
    book.available_stock = new_available
    db.session.commit()
    return book, None
