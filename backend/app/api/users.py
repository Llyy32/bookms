"""
users 模块。

在后端项目中的作用：
1. 提供用户管理（查询、创建、编辑、状态变更）的 REST API 入口（管理员专用）。
2. 提供普通用户自助更新个人资料与修改密码的入口。

优化建议：
- 增加批量禁用接口。
- 用户列表支持按注册时间、角色、状态排序。
"""

from flask import Blueprint, jsonify, request, session

from app.auth.decorators import admin_required, login_required
from app.services.user_service import (
    change_own_password,
    create_user,
    get_user,
    list_users,
    toggle_user_status,
    update_own_profile,
    update_user,
    user_to_dict,
)

bp = Blueprint("users", __name__)


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


# ─── 管理员接�� ───────────────────────────────────────────────


@bp.get("")
@admin_required
def list_users_api():
    """分页查询用户列表，支持关键词、角色、状态过滤（管理员）。"""
    try:
        page = max(1, int(request.args.get("page", 1) or 1))
        per_page = min(100, max(1, int(request.args.get("per_page", 20) or 20)))
    except (TypeError, ValueError):
        return jsonify({"code": 40001, "message": "分页参数错误", "data": None}), 400

    keyword = (request.args.get("keyword") or "").strip()
    role = (request.args.get("role") or "").strip()
    status_raw = request.args.get("status")
    status: object = None
    if status_raw in ("0", "1"):
        status = int(status_raw)

    result = list_users(
        page=page, per_page=per_page, keyword=keyword, role=role, status=status
    )
    return jsonify({"code": 0, "message": "ok", "data": result})


@bp.get("/<int:user_id>")
@admin_required
def get_user_api(user_id: int):
    """查询指定用户详情（管理员）。"""
    user = get_user(user_id)
    if not user:
        return jsonify({"code": 40401, "message": "用户不存在", "data": None}), 404
    return jsonify({"code": 0, "message": "ok", "data": user_to_dict(user)})


@bp.post("")
@admin_required
def create_user_api():
    """管理员创建用户。"""
    payload, err = _parse_json_body()
    if err:
        return jsonify({"code": 40001, "message": err, "data": None}), 400

    user, err = create_user(payload)
    if err:
        code = 40901 if "已存在" in err else 40001
        status = 409 if code == 40901 else 400
        return jsonify({"code": code, "message": err, "data": None}), status
    return jsonify({"code": 0, "message": "ok", "data": user_to_dict(user)}), 201


@bp.put("/<int:user_id>")
@admin_required
def update_user_api(user_id: int):
    """编辑用户信息，含角色变更与密码重置（管理员）。"""
    payload, err = _parse_json_body()
    if err:
        return jsonify({"code": 40001, "message": err, "data": None}), 400

    operator_id = int(session["user_id"])
    user, err = update_user(user_id, payload, operator_id)
    if err:
        if "不存在" in err:
            return jsonify({"code": 40401, "message": err, "data": None}), 404
        return jsonify({"code": 40001, "message": err, "data": None}), 400
    return jsonify({"code": 0, "message": "ok", "data": user_to_dict(user)})


@bp.patch("/<int:user_id>/status")
@admin_required
def toggle_status_api(user_id: int):
    """启用或禁用用户（管理员，不能操作自己）。"""
    payload, err = _parse_json_body()
    if err:
        return jsonify({"code": 40001, "message": err, "data": None}), 400

    status_val = payload.get("status")
    if status_val not in (0, 1):
        return jsonify({"code": 40001, "message": "status 必须是 0 或 1", "data": None}), 400

    operator_id = int(session["user_id"])
    err = toggle_user_status(user_id, status_val, operator_id)
    if err:
        if "不存在" in err:
            return jsonify({"code": 40401, "message": err, "data": None}), 404
        return jsonify({"code": 40001, "message": err, "data": None}), 400
    return jsonify({"code": 0, "message": "ok", "data": None})


# ─── 普通用户自助接口 ─────────────────────────────────────────


@bp.put("/me")
@login_required
def update_own_profile_api():
    """当前用户更新个人资料（real_name、phone、email）。"""
    payload, err = _parse_json_body()
    if err:
        return jsonify({"code": 40001, "message": err, "data": None}), 400

    user_id = int(session["user_id"])
    user, err = update_own_profile(user_id, payload)
    if err:
        return jsonify({"code": 40001, "message": err, "data": None}), 400
    return jsonify({"code": 0, "message": "ok", "data": user_to_dict(user)})


@bp.patch("/me/password")
@login_required
def change_password_api():
    """当前用户修改密码，需要验证旧密码。"""
    payload, err = _parse_json_body()
    if err:
        return jsonify({"code": 40001, "message": err, "data": None}), 400

    old_password = payload.get("old_password") or ""
    new_password = payload.get("new_password") or ""
    if not old_password or not new_password:
        return jsonify({"code": 40001, "message": "old_password 和 new_password 均不能为空", "data": None}), 400

    user_id = int(session["user_id"])
    err = change_own_password(user_id, old_password, new_password)
    if err:
        return jsonify({"code": 40001, "message": err, "data": None}), 400
    return jsonify({"code": 0, "message": "ok", "data": None})
