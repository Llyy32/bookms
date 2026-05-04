"""
健康检查接口模块。

在后端项目中的作用：
1. 提供最基础的服务可用性探针。
2. 用于本地联调、部署后巡检与监控系统探活。

可扩展建议：
- 增加数据库连通性检测。
- 增加版本号与构建信息返回。
"""

from flask import Blueprint, jsonify

bp = Blueprint("health", __name__)


@bp.get("/health")
def health():
    """返回服务健康状态。"""
    return jsonify({"code": 0, "message": "ok", "data": {"status": "up"}})
