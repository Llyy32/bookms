"""
扩展实例管理模块。

在后端项目中的作用：
1. 统一持有数据库、迁移等扩展单例，避免循环导入问题。
2. 作为 app factory 的配套模块，支持惰性初始化。

可扩展建议：
- 后续可在此增加缓存、任务队列、限流等扩展。
"""

from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema

db = SQLAlchemy()
migrate = Migrate()


class BaseSchema(Schema):
    """序列化基类，后续可放通用字段和序列化规则。"""

    pass
