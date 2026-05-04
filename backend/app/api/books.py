"""
books 模块。

在后端项目中的作用：
1. 提供图书 CRUD、分页搜索、库存调整和状态管理的 REST API 入口。
2. 权限控制：查询接口公开，写操作均需管理员角色。

优化建议：
- 增加批量下架接口（P7 导入导出阶段统一处理）。
- GET /books 增加排序参数（按书名、库存、创建时间）。
"""

from flask import Blueprint, jsonify, request, session

from app.auth.decorators import admin_required
from app.services.book_service import (
    adjust_stock,
    book_to_dict,
    create_book,
    delete_book,
    get_book,
    list_books,
    restore_book,
    update_book,
)

bp = Blueprint("books", __name__)


def _parse_json_body():
    """解析 JSON 请求体，返回 (payload, error)。"""
    if not request.data:
        return {}, "请求体为空"
    payload = request.get_json(force=True, silent=True)
    if payload is None:
        return None, "请求体不是合法的 JSON"
    if not isinstance(payload, dict):
        return None, "请求体必须是 JSON 对象"
    return payload, None


@bp.get("")
def list_books_api():
    """图书分页查询，支持关键词搜索和分类筛选；管理员可见下架图书。"""
    try:
        page = max(1, int(request.args.get("page", 1) or 1))
        per_page = min(100, max(1, int(request.args.get("per_page", 20) or 20)))
    except (TypeError, ValueError):
        return jsonify({"code": 40001, "message": "page/per_page 参数错误", "data": None}), 400

    keyword = (request.args.get("keyword") or "").strip()
    category = (request.args.get("category") or "").strip()
    include_offline = session.get("role") == "ADMIN"

    result = list_books(
        page=page,
        per_page=per_page,
        keyword=keyword,
        category=category,
        include_offline=include_offline,
    )
    return jsonify({"code": 0, "message": "ok", "data": result})


@bp.get("/<int:book_id>")
def get_book_api(book_id: int):
    """查询图书详情。"""
    book = get_book(book_id)
    if not book:
        return jsonify({"code": 40401, "message": "图书不存在", "data": None}), 404
    return jsonify({"code": 0, "message": "ok", "data": book_to_dict(book)})


@bp.post("")
@admin_required
def create_book_api():
    """新增图书（管理员）。"""
    payload, err = _parse_json_body()
    if err:
        return jsonify({"code": 40001, "message": err, "data": None}), 400

    book, err = create_book(payload)
    if err:
        code = 40901 if "已存在" in err else 40001
        status = 409 if code == 40901 else 400
        return jsonify({"code": code, "message": err, "data": None}), status
    return jsonify({"code": 0, "message": "ok", "data": book_to_dict(book)}), 201


@bp.put("/<int:book_id>")
@admin_required
def update_book_api(book_id: int):
    """编辑图书基本信息（管理员）。"""
    payload, err = _parse_json_body()
    if err:
        return jsonify({"code": 40001, "message": err, "data": None}), 400

    book, err = update_book(book_id, payload)
    if err:
        if "不存在" in err:
            return jsonify({"code": 40401, "message": err, "data": None}), 404
        if "已存在" in err:
            return jsonify({"code": 40901, "message": err, "data": None}), 409
        return jsonify({"code": 40001, "message": err, "data": None}), 400
    return jsonify({"code": 0, "message": "ok", "data": book_to_dict(book)})


@bp.delete("/<int:book_id>")
@admin_required
def delete_book_api(book_id: int):
    """下架图书（管理员，软删除 status=0）。"""
    err = delete_book(book_id)
    if err:
        code = 40401 if "不存在" in err else 40901
        status = 404 if code == 40401 else 409
        return jsonify({"code": code, "message": err, "data": None}), status
    return jsonify({"code": 0, "message": "ok", "data": None})


@bp.patch("/<int:book_id>/restore")
@admin_required
def restore_book_api(book_id: int):
    """恢复下架图书上架（管理员，status 0→1）。"""
    err = restore_book(book_id)
    if err:
        code = 40401 if "不存在" in err else 40901
        status = 404 if code == 40401 else 409
        return jsonify({"code": code, "message": err, "data": None}), status
    book = get_book(book_id)
    return jsonify({"code": 0, "message": "ok", "data": book_to_dict(book)})


@bp.patch("/<int:book_id>/stock")
@admin_required
def adjust_stock_api(book_id: int):
    """调整图书库存（管理员），delta 正数增加、负数减少。"""
    payload, err = _parse_json_body()
    if err:
        return jsonify({"code": 40001, "message": err, "data": None}), 400

    try:
        delta = int(payload.get("delta", 0))
    except (TypeError, ValueError):
        return jsonify({"code": 40001, "message": "delta 必须是整数", "data": None}), 400

    if delta == 0:
        return jsonify({"code": 40001, "message": "delta 不能为 0", "data": None}), 400

    book, err = adjust_stock(book_id, delta)
    if err:
        code = 40401 if "不存在" in err else 40901
        status = 404 if code == 40401 else 409
        return jsonify({"code": code, "message": err, "data": None}), status
    return jsonify({"code": 0, "message": "ok", "data": book_to_dict(book)})
