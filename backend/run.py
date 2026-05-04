"""
应用启动入口。

在后端项目中的作用：
1. 提供本地开发时最直接的 Flask 启动方式。
2. 统一创建 app 实例，便于后续接入 gunicorn/uwsgi。

可扩展建议：
- 增加环境变量端口读取，避免硬编码端口。
- 区分 dev/test/prod 启动参数。
"""

from app import create_app

app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
