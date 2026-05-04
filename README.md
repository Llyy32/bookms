# bookMS

`bookMS` 是一个基于 `Flask API + Vue3` 的前后端分离图书管理系统。

## 一、项目定位

- 面向中小型图书馆、阅览室或校园图书室的基础业务管理
- 支持管理员与普通用户两类角色
- 以图书管理、借阅归还、预约、统计分析、导入导出为核心功能

## 二、技术栈

| 层 | 技术 |
|---|---|
| 后端框架 | Python Flask（RESTful API） |
| 前端框架 | Vue3 + TypeScript + Pinia + Element Plus |
| 图表库 | ECharts 5 |
| 数据库 | MySQL |
| 认证方式 | Session / Cookie |

## 三、业务规则

- 用户可自助注册，注册后可完善个人资料
- 最大借阅册数：`5`，借阅周期：`30` 天
- 逾期处理：仅标记 + 借阅限制，不启用罚金
- 预约规则：有库存也可预约，预约有效期 `3` 天
- 报表口径：借阅排行榜、逾期统计、库存统计、用户活跃度

## 四、功能进度

| 序号 | 功能块 | 状态 |
|------|--------|------|
| P1 | 认证与会话（注册、登录、退出、/me） | ✅ 已完成 |
| P2 | 图书管理（CRUD + 分页搜索 + 分类 + 库存调整） | ✅ 已完成 |
| P3 | 用户管理（管理员管理 + 自助资料 + 改密码） | ✅ 已完成 |
| P4 | 借阅归还（借书、还书、逾期懒标记） | ✅ 已完成 |
| P5 | 预约管理（预约、取消、到期懒标记、借阅自动履行） | ✅ 已完成 |
| P6 | 报表统计（借阅排行、逾期、库存、用户活跃度） | ✅ 已完成 |
| P7 | 导入导出（图书/用户/借阅记录 CSV） | 待开发 |

## 五、项目结构

```
bookms/
├── backend/
│   ├── app/
│   │   ├── api/            # 路由层
│   │   │   ├── auth.py         # 认证接口
│   │   │   ├── books.py        # 图书接口
│   │   │   ├── users.py        # 用户接口
│   │   │   ├── borrow_records.py  # 借阅接口
│   │   │   ├── reservations.py    # 预约接口
│   │   │   └── reports.py         # 报表接口
│   │   ├── services/       # 业务逻辑层
│   │   │   ├── auth_service.py
│   │   │   ├── book_service.py
│   │   │   ├── user_service.py
│   │   │   ├── borrow_service.py
│   │   │   ├── reservation_service.py
│   │   │   └── report_service.py
│   │   ├── models/         # ORM 模型
│   │   │   ├── user.py
│   │   │   ├── book.py
│   │   │   ├── borrow_record.py
│   │   │   └── reservation.py
│   │   └── auth/           # 登录态装饰器
│   ├── sql/
│   │   └── init.sql        # 数据库初始化脚本（数据库名：bookms）
│   ├── config.py
│   ├── run.py
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── api/            # 后端接口封装
│       │   ├── http.ts
│       │   ├── books.ts
│       │   ├── users.ts
│       │   ├── borrowRecords.ts
│       │   └── reservations.ts
│       ├── layouts/
│       │   └── AppLayout.vue   # 侧边栏 + 顶栏 Shell
│       ├── views/
│       │   ├── LoginView.vue
│       │   ├── BooksView.vue       # 图书管理（含借阅/预约入口）
│       │   ├── UsersView.vue       # 用户管理（管理员）
│       │   ├── BorrowView.vue      # 借阅记录
│       │   ├── ReservationsView.vue # 预约管理
│       │   ├── ReportsView.vue     # 报表统计（ECharts 图表）
│       │   └── ProfileView.vue     # 个人资料 + 我的借阅
│       ├── stores/
│       │   └── auth.ts
│       └── router/
│           └── index.ts
├── docs/                   # 设计文档
└── CLAUDE.md
```

## 六、快速启动

### 环境要求

- Python 3.10+
- Node.js 18+
- MySQL 8.0+

### 后端

```bash
cd backend
pip install -r requirements.txt
copy .env.example .env    # Windows
# cp .env.example .env    # Linux/macOS
# 编辑 .env 填写数据库连接信息
python run.py
```

### 数据库初始化

```bash
mysql -u root -p bookms < backend/sql/init.sql
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

### 演示账号（种子数据）

执行 `backend/sql/init.sql` 后可用以下账号登录，密码均为 `BookMS@demo123`：

| 账号 | 角色 |
|------|------|
| admin | 管理员 |
| user001 | 普通用户 |
| user002 | 普通用户 |

## 七、前端路由说明

| 路径 | 页面 | 权限 |
|------|------|------|
| `/login` | 登录页 | 公开 |
| `/books` | 图书管理 | 登录用户 |
| `/users` | 用户管理 | 管理员 |
| `/borrows` | 借阅记录 | 登录用户 |
| `/reservations` | 预约管理 | 登录用户 |
| `/reports` | 报表统计 | 管理员 |
| `/profile` | 个人资料 | 登录用户 |

## 八、API 前缀

所有接口统一挂载在 `/api/v1` 下，详见 `docs/05-后端API设计.md`。

## 九、文档目录

- `docs/01-项目概述.md`
- `docs/02-需求规格说明书.md`
- `docs/03-系统架构设计.md`
- `docs/04-数据库设计.md`
- `docs/05-后端API设计.md`
- `docs/06-前端设计说明.md`
- `docs/07-开发与协作规范.md`
- `docs/08-测试计划.md`（含各功能块手工验证清单）
- `docs/09-环境与运行部署说明.md`

## 十、后续待开发

- P7：导入导出（图书/用户/借阅记录 CSV）
- 消息通知（预约到书、借阅即将到期提醒）
- 权限细化（菜单级、接口级）
- 审计日志与操作追溯
- Linux 部署方案
