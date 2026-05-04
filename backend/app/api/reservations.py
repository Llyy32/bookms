"""
reservations 模块。

在后端项目中的作用：
1. 提供预约创建、取消、列表查询与详情查询的 REST API 入口。
2. 权限控制：预约/取消需登录，管理员可查看全部预约。

优化建议：
- 增加管理员批量清理到期预约接口。
- 增加预约排队顺序字段，支持公平排队取书。
"""

from flask import Blueprint, jsonify, request, session

from app.auth.decorators import login_required
from app.services.reservation_service import (
    cancel_reservation,
    create_reservation,
    get_reservation,
    list_reservations,
    reservation_to_dict,
)

bp = Blueprint("reservations", __name__)


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
def create_reservation_api():
    """创建预约，有库存也允许（登录用户）。"""
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
    reservation, err = create_reservation(user_id, book_id)
    if err:
        code = 40901 if "已对该书" in err or "已下架" in err else 40001
        status = 409 if code == 40901 else 400
        return jsonify({"code": code, "message": err, "data": None}), status
    return jsonify({"code": 0, "message": "ok", "data": reservation_to_dict(reservation)}), 201


@bp.post("/<int:reservation_id>/cancel")
@login_required
def cancel_reservation_api(reservation_id: int):
    """取消预约，仅 ACTIVE 状态可取消，本人或管理员操作。"""
    user_id = int(session["user_id"])
    is_admin = session.get("role") == "ADMIN"
    reservation, err = cancel_reservation(reservation_id, user_id, is_admin)
    if err:
        if "不存在" in err:
            return jsonify({"code": 40401, "message": err, "data": None}), 404
        if "无权" in err:
            return jsonify({"code": 40301, "message": err, "data": None}), 403
        return jsonify({"code": 40901, "message": err, "data": None}), 409
    return jsonify({"code": 0, "message": "ok", "data": reservation_to_dict(reservation)})


@bp.get("")
@login_required
def list_reservations_api():
    """查询预约记录：管理员可查全部，普通用户只查本人。"""
    try:
        page = max(1, int(request.args.get("page", 1) or 1))
        per_page = min(100, max(1, int(request.args.get("per_page", 20) or 20)))
    except (TypeError, ValueError):
        return jsonify({"code": 40001, "message": "分页参数错误", "data": None}), 400

    is_admin = session.get("role") == "ADMIN"
    current_user_id = int(session["user_id"])

    if is_admin:
        uid_param = request.args.get("user_id")
        user_id = int(uid_param) if uid_param else None
    else:
        user_id = current_user_id

    status = (request.args.get("status") or "").strip()
    book_keyword = (request.args.get("keyword") or "").strip()

    result = list_reservations(
        page=page,
        per_page=per_page,
        user_id=user_id,
        status=status,
        book_keyword=book_keyword,
    )
    return jsonify({"code": 0, "message": "ok", "data": result})


@bp.get("/<int:reservation_id>")
@login_required
def get_reservation_api(reservation_id: int):
    """查询预约详情，普通用户只能查看本人的预约。"""
    reservation = get_reservation(reservation_id)
    if not reservation:
        return jsonify({"code": 40401, "message": "预约记录不存在", "data": None}), 404

    is_admin = session.get("role") == "ADMIN"
    current_user_id = int(session["user_id"])
    if not is_admin and reservation.user_id != current_user_id:
        return jsonify({"code": 40301, "message": "无权查看此预约记录", "data": None}), 403

    return jsonify({"code": 0, "message": "ok", "data": reservation_to_dict(reservation)})
