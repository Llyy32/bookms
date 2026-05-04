"""
认证接口模块。

在后端项目中的作用：
1. 提供注册、登录、退出和当前用户查询入口。
2. 以 Session/Cookie 为认证基础，承载用户身份态。

可扩展建议：
- 增加登录失败次数限制、验证码、审计日志。
- 接入双因素认证与密码找回流程。
"""

from flask import Blueprint, jsonify, request, session

from app.services.auth_service import (
    authenticate_user,
    get_user_by_id,
    register_user,
    user_to_public,
)

bp = Blueprint("auth", __name__)


def _parse_json_body():
    """
    解析 JSON 请求体。

    Postman 若未选 application/json，默认可能不带正确 Content-Type，
    使用 force=True 仍可解析正文，避免 username/password 被误判为空。
    """
    if not request.data:
        return {}, "请求体为空，请发送 JSON，例如 {\"username\":\"...\",\"password\":\"...\"}"
    payload = request.get_json(force=True, silent=True)
    if payload is None:
        return None, "请求体不是合法的 JSON，请检查逗号、引号是否完整，并建议使用 Content-Type: application/json"
    if not isinstance(payload, dict):
        return None, "请求体必须是 JSON 对象"
    return payload, None


@bp.post("/register")
def register():
    """用户自助注册，默认角色为 USER，密码经哈希后入库。"""
    payload, parse_err = _parse_json_body()
    if parse_err:
        return jsonify({"code": 40001, "message": parse_err, "data": None}), 400
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""
    if not username or not password:
        return (
            jsonify(
                {
                    "code": 40001,
                    "message": "缺少 username 或 password，且请确认 Body 类型为 raw + JSON",
                    "data": None,
                }
            ),
            400,
        )
    user, err, code = register_user(
        username,
        password,
        real_name=(payload.get("real_name") or "").strip() or None,
        phone=(payload.get("phone") or "").strip() or None,
        email=(payload.get("email") or "").strip() or None,
    )
    if err:
        status = 409 if code == "40901" else 400
        return jsonify({"code": int(code or "40001"), "message": err, "data": None}), status
    return jsonify({"code": 0, "message": "ok", "data": user_to_public(user)}), 201


@bp.post("/login")
def login():
    """用户名密码登录，成功后写入 Session（user_id、username、role）。"""
    payload, parse_err = _parse_json_body()
    if parse_err:
        return jsonify({"code": 40001, "message": parse_err, "data": None}), 400
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""
    if not username or not password:
        return (
            jsonify(
                {
                    "code": 40001,
                    "message": "缺少 username 或 password",
                    "data": None,
                }
            ),
            400,
        )
    user, err, code = authenticate_user(username, password)
    if err:
        status = 403 if code == "40301" else 401
        return jsonify({"code": int(code or "40101"), "message": err, "data": None}), status

    session.permanent = True
    session["user_id"] = user.id
    session["username"] = user.username
    session["role"] = user.role
    return jsonify({"code": 0, "message": "ok", "data": user_to_public(user)})


@bp.post("/logout")
def logout():
    """清理当前会话并退出登录。"""
    session.clear()
    return jsonify({"code": 0, "message": "ok", "data": None})


@bp.get("/me")
def me():
    """根据 Session 中的 user_id 返回数据库中的最新用户信息。"""
    uid = session.get("user_id")
    if not uid:
        return jsonify({"code": 40101, "message": "未登录或会话已失效", "data": None}), 401
    user = get_user_by_id(int(uid))
    if not user:
        session.clear()
        return jsonify({"code": 40101, "message": "未登录或会话已失效", "data": None}), 401
    if user.status != 1:
        session.clear()
        return jsonify({"code": 40301, "message": "账号已禁用", "data": None}), 403
    return jsonify({"code": 0, "message": "ok", "data": user_to_public(user)})
