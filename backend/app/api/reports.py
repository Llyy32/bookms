"""
reports 模块。

在后端项目中的作用：
1. 提供借阅排行、逾期统计、库存统计、用户活跃度四类报表 API 入口。
2. 全部接口仅限管理员访问，支持可选时间范围筛选。

优化建议：
- 增加 ETag / Last-Modified 响应头，配合前端缓存减少重复统计查询。
- 时间范围参数校验可统一抽取为装饰器或工具函数。
"""

from flask import Blueprint, jsonify, request

from app.auth.decorators import admin_required
from app.services.report_service import (
    get_borrow_ranking,
    get_overdue_summary,
    get_stock_summary,
    get_user_activity,
)

bp = Blueprint("reports", __name__)


def _get_date_range():
    """从查询参数中提取 start / end 日期字符串，返回 (start, end)。"""
    start = (request.args.get("start") or "").strip() or None
    end = (request.args.get("end") or "").strip() or None
    return start, end


def _get_limit(default: int = 20, max_val: int = 100) -> int:
    """从查询参数中提取 limit，越界时截断。"""
    try:
        return min(max_val, max(1, int(request.args.get("limit", default) or default)))
    except (TypeError, ValueError):
        return default


@bp.get("/borrow-ranking")
@admin_required
def borrow_ranking():
    """
    借阅排行榜：图书被借阅次数降序，支持时间范围和条数过滤。

    Query params: start, end (YYYY-MM-DD), limit (默认 20)
    """
    start, end = _get_date_range()
    limit = _get_limit()
    data = get_borrow_ranking(limit=limit, start_str=start, end_str=end)
    return jsonify({"code": 0, "message": "ok", "data": data})


@bp.get("/overdue-summary")
@admin_required
def overdue_summary():
    """
    逾期统计：总逾期数、当前逾期数、历史逾期已还数，及逾期最多图书 Top10。

    Query params: start, end (YYYY-MM-DD)
    """
    start, end = _get_date_range()
    data = get_overdue_summary(start_str=start, end_str=end)
    return jsonify({"code": 0, "message": "ok", "data": data})


@bp.get("/stock-summary")
@admin_required
def stock_summary():
    """库存统计：全库总册数、可借、在借，以及按分类汇总（无时间范围参数）。"""
    data = get_stock_summary()
    return jsonify({"code": 0, "message": "ok", "data": data})


@bp.get("/user-activity")
@admin_required
def user_activity():
    """
    用户活跃度：按借阅次数降序的用户排行，支持时间范围和条数过滤。

    Query params: start, end (YYYY-MM-DD), limit (默认 20)
    """
    start, end = _get_date_range()
    limit = _get_limit()
    data = get_user_activity(limit=limit, start_str=start, end_str=end)
    return jsonify({"code": 0, "message": "ok", "data": data})
