# 05 后端 API 设计

## 5.1 统一约定

- 基础前缀：`/api/v1`
- 认证方式：`Session/Cookie`
- 数据格式：`application/json`

统一响应示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {}
}
```

## 5.2 认证接口

- `POST /auth/register` 用户注册
- `POST /auth/login` 账号登录
- `POST /auth/logout` 退出登录
- `GET /auth/me` 获取当前登录用户信息

## 5.3 用户接口

- `GET /users` 管理员查询用户列表
- `GET /users/{id}` 查询用户详情
- `POST /users` 管理员创建用户
- `PUT /users/{id}` 更新用户信息
- `PATCH /users/{id}/status` 启用/禁用用户

## 5.4 图书接口

- `GET /books` 图书分页查询（支持关键词）
- `GET /books/{id}` 图书详情
- `POST /books` 新增图书（管理员）
- `PUT /books/{id}` 编辑图书（管理员）
- `DELETE /books/{id}` 删除/下架图书（管理员）
- `PATCH /books/{id}/stock` 调整库存（管理员）

## 5.5 借阅接口

- `POST /borrow-records` 创建借阅
  - 校验登录态、库存、借阅上限、逾期限制
  - 默认应还时间：借阅时间 + 30 天
- `POST /borrow-records/{id}/return` 归还图书
- `GET /borrow-records` 查询借阅记录（管理员可查全部，用户查本人）
- `GET /borrow-records/{id}` 借阅详情

## 5.6 预约接口

- `POST /reservations` 创建预约（有库存也允许）
- `POST /reservations/{id}/cancel` 取消预约
- `GET /reservations` 查询预约列表
- `GET /reservations/{id}` 查询预约详情

## 5.7 报表接口

- `GET /reports/borrow-ranking` 借阅排行榜
- `GET /reports/overdue-summary` 逾期统计
- `GET /reports/stock-summary` 库存统计
- `GET /reports/user-activity` 用户活跃度

## 5.8 导入导出接口

- `POST /imports/books` 导入图书
- `POST /imports/users` 导入用户
- `POST /imports/borrow-records` 导入借阅记录
- `GET /exports/books` 导出图书
- `GET /exports/users` 导出用户
- `GET /exports/borrow-records` 导出借阅记录

## 5.9 错误码建议

- `0`：成功
- `40001`：参数错误
- `40101`：未登录或会话失效
- `40301`：无权限
- `40401`：资源不存在
- `40901`：业务冲突（库存不足、超过借阅上限等）
- `50000`：服务器内部错误
