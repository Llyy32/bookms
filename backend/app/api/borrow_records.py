"""
borrow_records 模块。

在后端项目中的作用：
1. 提供借阅创建、归还、列表查询与详情查询的 REST API 入口。
2. 权限控制：借阅/归还需登录，查询全部记录需管理员角色。

优化建议：
- 增加管理员代借接口（指定 user_id）。
- 增加批量归还接口供图书管理场景使用。
"""

from flask import Blueprint, jsonify, request, session

from app.auth.decorators import login_required
from app.services.borrow_service import (
    borrow_to_dict,
    create_borrow,
    get_borrow,
    list_borrows,
    return_borrow,
)

bp = Blueprint("borrow_records", __name__)


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


@bp.post("")
@login_required
def create_borrow_api():
    """创建借阅记录，含库存/上限/逾期全部业务校验（登录用户）。"""
    payload, err = _parse_json_body()
    if err:
        return jsonify({"code": 40001, "message": err, "data": None}), 400

    book_id = payload.get("book_id")
    if not book_id:
        return jsonify({"code": 40001, "message": "book_id 不能为空", "data": None}), 400
    try:
        book_id = int(book_id)
    except (TypeError, ValueError):
        return jsonify({"code": 40001, "message": "book_id 必须是整数", "data": None}), 400

    user_id = int(session["user_id"])
    record, err = create_borrow(user_id, book_id)
    if err:
        return jsonify({"code": 40901, "message": err, "data": None}), 409
    return jsonify({"code": 0, "message": "ok", "data": borrow_to_dict(record)}), 201


@bp.post("/<int:record_id>/return")
@login_required
def return_borrow_api(record_id: int):
    """归还图书，库存原子加 1（本人或管理员可操作）。"""
    user_id = int(session["user_id"])
    is_admin = session.get("role") == "ADMIN"
    record, err = return_borrow(record_id, user_id, is_admin)
    if err:
        if "不存在" in err:
            return jsonify({"code": 40401, "message": err, "data": None}), 404
        if "无权" in err:
            return jsonify({"code": 40301, "message": err, "data": None}), 403
        return jsonify({"code": 40901, "message": err, "data": None}), 409
    return jsonify({"code": 0, "message": "ok", "data": borrow_to_dict(record)})


@bp.get("")
@login_required
def list_borrows_api():
    """查询借阅记录：管理员可查全部并按 user_id 过滤，普通用户只查本人。"""
    try:
        page = max(1, int(request.args.get("page", 1) or 1))
        per_page = min(100, max(1, int(request.args.get("per_page", 20) or 20)))
    except (TypeError, ValueError):
        return jsonify({"code": 40001, "message": "分页参数错误", "data": None}), 400

    is_admin = session.get("role") == "ADMIN"
    current_user_id = int(session["user_id"])

    # 普通用户只能看自己的记录
    if is_admin:
        uid_param = request.args.get("user_id")
        user_id = int(uid_param) if uid_param else None
    else:
        user_id = current_user_id

    status = (request.args.get("status") or "").strip()
    book_keyword = (request.args.get("keyword") or "").strip()

    result = list_borrows(
        page=page,
        per_page=per_page,
        user_id=user_id,
        status=status,
        book_keyword=book_keyword,
    )
    return jsonify({"code": 0, "message": "ok", "data": result})


@bp.get("/<int:record_id>")
@login_required
def get_borrow_api(record_id: int):
    """查询借阅详情，普通用户只能查看本人的记录。"""
    record = get_borrow(record_id)
    if not record:
        return jsonify({"code": 40401, "message": "借阅记录不存在", "data": None}), 404

    is_admin = session.get("role") == "ADMIN"
    current_user_id = int(session["user_id"])
    if not is_admin and record.user_id != current_user_id:
        return jsonify({"code": 40301, "message": "无权查看此借阅记录", "data": None}), 403

    return jsonify({"code": 0, "message": "ok", "data": borrow_to_dict(record)})
