"""
模型聚合导出模块。

在后端项目中的作用：
1. 统一导出所有 ORM 模型，便于外部按包导入。
2. 为迁移工具和业务模块提供集中模型入口。

可扩展建议：
- 模型增多后可按领域拆分子包并在此聚合导出。
"""

from .book import Book
from .borrow_record import BorrowRecord
from .reservation import Reservation
from .user import User

__all__ = ["User", "Book", "BorrowRecord", "Reservation"]
