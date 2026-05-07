# 项目智能管家（Hermes Agent）— 技术规格说明书

> 基于 FPA 分析的四层技术转化
> 目标架构：Python FastAPI + PostgreSQL + Redis + 飞书 API + Git Webhook
> 交付策略：MVP（飞书消息交互，无独立前端）

---

## 第一层：数据层 — 数据库设计

### 约束
- 数据库：PostgreSQL 15+
- 命名：snake_case
- 主键：UUID v4（字符串）或 BIGSERIAL
- 金额/计数：INTEGER 或 BIGINT
- 时间：TIMESTAMP WITH TIME ZONE，统一 UTC
- JSON 扩展：JSONB 类型

### 表结构

#### projects（项目）
| 字段 | 类型 | 约束 | 说明 |
|:---|:---|:---:|:---|
| id | UUID | PK | 项目唯一ID |
| topic_id | VARCHAR(10) | UNIQUE NOT NULL | 话题编号如 #001 |
| name | VARCHAR(200) | NOT NULL | 项目名称 |
| description | TEXT | - | 项目描述 |
| tech_stack | JSONB | - | 技术栈列表 |
| repo_path | VARCHAR(500) | - | 本地路径或 Git 地址 |
| status | VARCHAR(20) | DEFAULT 'active' | active/archived/completed |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | |

#### tasks（任务）
| 字段 | 类型 | 约束 | 说明 |
|:---|:---|:---:|:---|
| id | UUID | PK | |
| project_id | UUID | FK→projects | 关联项目 |
| title | VARCHAR(300) | NOT NULL | 任务标题 |
| description | TEXT | - | 任务描述 |
| source | VARCHAR(50) | - | 来源：chat/commit/meeting/manual |
| status | VARCHAR(20) | DEFAULT 'todo' | todo/in_progress/done |
| priority | VARCHAR(10) | DEFAULT 'P2' | P0/P1/P2/P3 |
| feishu_record_id | VARCHAR(100) | - | 飞书多维表格记录ID |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | |
| completed_at | TIMESTAMPTZ | - | |

#### capabilities（原子能力）
| 字段 | 类型 | 约束 | 说明 |
|:---|:---|:---:|:---|
| id | UUID | PK | |
| cap_id | VARCHAR(20) | UNIQUE NOT NULL | 能力编号如 CAP-001 |
| name | VARCHAR(200) | NOT NULL | 能力名称 |
| description | TEXT | - | 功能描述 |
| input_schema | JSONB | - | 输入参数定义 |
| output_schema | JSONB | - | 输出格式定义 |
| call_type | VARCHAR(20) | NOT NULL | api/script/snippet |
| call_definition | TEXT | - | 调用方式（API地址/脚本路径/代码） |
| source_project_id | UUID | FK→projects | 来源项目 |
| feishu_record_id | VARCHAR(100) | - | 飞书记录ID |
| status | VARCHAR(20) | DEFAULT 'draft' | draft/published/deprecated |
| version | INTEGER | DEFAULT 1 | 当前版本号 |
| usage_count | INTEGER | DEFAULT 0 | 累计调用次数 |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | |

**索引**：`(name gin_trgm_ops)` 用于模糊搜索，`(status, usage_count)` 用于报告查询

#### cap_versions（能力版本）
| 字段 | 类型 | 约束 | 说明 |
|:---|:---|:---:|:---|
| id | UUID | PK | |
| capability_id | UUID | FK→capabilities | |
| version | INTEGER | NOT NULL | 版本号 |
| change_log | TEXT | - | 变更说明 |
| snapshot | JSONB | - | 该版本的完整配置快照 |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | |

#### cap_usage_logs（能力调用日志）
| 字段 | 类型 | 约束 | 说明 |
|:---|:---|:---:|:---|
| id | UUID | PK | |
| capability_id | UUID | FK→capabilities | |
| project_id | UUID | FK→projects | 调用方项目 |
| context | VARCHAR(200) | - | 调用场景描述 |
| feedback | VARCHAR(20) | - | useful/useless/null |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | |

#### doc_links（文档关联）
| 字段 | 类型 | 约束 | 说明 |
|:---|:---|:---:|:---|
| id | UUID | PK | |
| feishu_doc_token | VARCHAR(100) | NOT NULL | 飞书文档token |
| feishu_doc_title | VARCHAR(300) | - | |
| linked_type | VARCHAR(20) | NOT NULL | capability/repo/wiki |
| linked_id | VARCHAR(100) | - | 能力ID/仓库路径 |
| linked_url | VARCHAR(500) | - | 链接URL |
| last_checked_at | TIMESTAMPTZ | - | 上次检查时间 |
| is_valid | BOOLEAN | DEFAULT true | 链接有效 |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | |

#### audit_logs（操作日志）
| 字段 | 类型 | 约束 | 说明 |
|:---|:---|:---:|:---|
| id | BIGSERIAL | PK | |
| action | VARCHAR(50) | NOT NULL | 操作名如 task.create / cap.publish |
| entity_type | VARCHAR(50) | - | 实体类型 |
| entity_id | VARCHAR(100) | - | 实体ID |
| before_snapshot | JSONB | - | 操作前快照 |
| after_snapshot | JSONB | - | 操作后快照 |
| performed_by | VARCHAR(100) | - | 操作人(飞书用户ID) |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | |

#### webhook_events（Webhook 事件）
| 字段 | 类型 | 约束 | 说明 |
|:---|:---|:---:|:---|
| id | BIGSERIAL | PK | |
| source | VARCHAR(50) | NOT NULL | github/gitlab |
| event_type | VARCHAR(50) | - | push/pull_request |
| raw_payload | JSONB | - | 原始事件数据 |
| processed | BOOLEAN | DEFAULT false | 是否已处理 |
| processed_at | TIMESTAMPTZ | - | |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | |

---

## 第二层：交互层 — API 接口设计

### 约束
- 统一响应格式：`{"code": 200, "msg": "成功", "data": ...}`
- 认证：飞书 App Ticket + Tenant Access Token
- 所有写操作记录 audit_logs
- 分页参数：`page`(1开始), `page_size`(默认20, 最大100)

### API 端点

#### 项目管理

| 功能点 | 路径 | 方法 | 核心参数 | 认证 | 优先级 |
|:---|:---|:---:|:---|:---:|:---:|
| 项目列表 | /api/projects | GET | page, page_size, status | 飞书token | P0 |
| 项目详情 | /api/projects/{id} | GET | - | 飞书token | P0 |
| 创建项目 | /api/projects | POST | {name, topic_id, tech_stack} | 飞书token | P0 |
| 更新项目 | /api/projects/{id} | PUT | 部分更新字段 | 飞书token | P1 |
| 归档项目 | /api/projects/{id}/archive | POST | - | 飞书token | P2 |
| 任务列表 | /api/projects/{id}/tasks | GET | page, status, priority | 飞书token | P0 |
| 创建任务 | /api/tasks | POST | {project_id, title, priority, source} | 飞书token | P0 |
| 更新任务状态 | /api/tasks/{id}/status | PUT | {status} | 飞书token | P0 |
| 批量同步到飞书看板 | /api/tasks/sync-feishu | POST | - | 飞书token | P0 |
| 生成周报 | /api/projects/{id}/weekly-report | GET | - | 飞书token | P1 |
| 生成会议纪要 | /api/meetings/minutes | POST | {meeting_content} | 飞书token | P1 |

#### 能力管理

| 功能点 | 路径 | 方法 | 核心参数 | 认证 | 优先级 |
|:---|:---|:---:|:---|:---:|:---:|
| 能力列表 | /api/capabilities | GET | page, status, q(搜索) | 飞书token | P0 |
| 能力详情 | /api/capabilities/{id} | GET | - | 飞书token | P0 |
| 创建能力 | /api/capabilities | POST | cap schema | 飞书token | P0 |
| 更新能力 | /api/capabilities/{id} | PUT | 更新字段+自动创建版本 | 飞书token | P2 |
| 搜索能力 | /api/capabilities/search | GET | q(自然语言), limit | 飞书token | P0 |
| 推荐能力 | /api/capabilities/recommend | POST | {project_context} | 飞书token | P0 |
| 记录反馈 | /api/capabilities/{id}/feedback | POST | {project_id, feedback} | 飞书token | P1 |
| 能力草稿列表 | /api/capabilities/drafts | GET | page | 飞书token | P0 |
| 确认草稿 | /api/capabilities/{id}/publish | POST | - | 飞书token | P0 |

#### 知识库

| 功能点 | 路径 | 方法 | 核心参数 | 认证 | 优先级 |
|:---|:---|:---:|:---|:---:|:---:|
| 创建文档关联 | /api/doc-links | POST | {doc_token, linked_type, linked_id} | 飞书token | P1 |
| 检查链接 | /api/doc-links/check | POST | - | 飞书token | P1 |
| 孤儿文档列表 | /api/doc-links/orphans | GET | - | 飞书token | P2 |
| 变更传播通知 | /api/doc-links/propagate | POST | {capability_id} | 飞书token | P1 |

#### 报告

| 功能点 | 路径 | 方法 | 核心参数 | 认证 | 优先级 |
|:---|:---|:---:|:---|:---:|:---:|
| 月度报告 | /api/reports/monthly | GET | year, month | 飞书token | P1 |
| 项目健康度 | /api/reports/health | GET | - | 飞书token | P2 |

#### Webhook & 系统

| 功能点 | 路径 | 方法 | 核心参数 | 认证 | 优先级 |
|:---|:---|:---:|:---|:---:|:---:|
| Git Webhook 入口 | /api/webhooks/git | POST | 原始payload | 签名验证 | P0 |
| 飞书事件入口 | /api/webhooks/feishu | POST | 事件payload | 飞书验证 | P0 |
| 操作日志查询 | /api/audit-logs | GET | page, entity_type | 飞书token | P0 |

---

## 第三层：逻辑层 — 验收标准 + 日志规范

### P0 验收标准

#### 1. 任务提取与飞书看板同步
```
Given 飞书对话中用户提到"#003 需要加一个搜索功能"或 Git commit 消息含"feat(#003): 添加搜索"
When Agent 监听到事件
Then 在 tasks 表创建一条记录，状态=todo，关联project_id=#003
And 调用飞书 API 写入《项目看板》多维表格
And audit_logs 记录操作前后快照
```

#### 2. 原子能力识别
```
Given Git Webhook 收到 push 事件
When commit 消息包含通用动词（如"add wechat pay""fix skew correction"）
And 类似操作在≥2个项目中出现
Then 在 capabilities 表创建一条 draft 状态记录
And 向飞书发送能力草稿确认消息
```

#### 3. 能力检索与推荐
```
Given 用户在飞书发送"需要裁图扶正"
When Agent 收到消息
Then 在 capabilities 表搜索匹配 name/description
And 返回匹配结果及调用方式
```

#### 4. 反馈记录
```
Given 用户点击飞书消息上的"有用"按钮
When Agent 收到反馈事件
Then cap_usage_logs.feedback 更新为 useful
And capabilities.usage_count +1
```

#### 5. 月度报告
```
Given 每月1日 00:00 定时任务触发
When Agent 查询上月 cap_usage_logs
Then 生成统计报告（调用次数、节省工时、未使用列表）
And 发送飞书消息给用户
```

### 日志规范

| 操作 | 实体类型 | 记录内容 |
|:---|:---|:---|
| 创建任务 | task | 完整任务对象 |
| 更新任务状态 | task | {before: status, after: status} |
| 创建能力 | capability | 完整能力对象 |
| 发布能力草稿 | capability | draft→published变更 |
| 同步飞书 | feishu_record | 同步的字段、飞书record_id |
| Webhook 接收 | webhook_event | 事件类型、来源 |

所有日志使用 `audit_logs` 表持久化，同时输出到 `stdout`（FastAPI logging）。

---

## 第四层：项目层 — 外部依赖 + 降级方案 + 技术组件

### 外部依赖

| 依赖项 | 关联功能 | 获取方式 | 降级方案 | 阶段 |
|:---|:---|:---|:---|:---:|
| 飞书多维表格 API | 项目看板、能力清单 | 飞书开放平台 | 失败时本地存储，手动同步 | MVP |
| 飞书消息 API | 推送推荐、反馈按钮 | 飞书开放平台 | - | MVP |
| Git Webhook | 代码变更监听 | GitHub/GitLab 设置 | 无公网时手动触发 | MVP |
| 大语言模型 | 任务提取/能力识别/检索 | Ollama 本地或 OpenAI | 降级为关键词匹配 | MVP |
| 公网隧道 | Git Webhook 可达 | ngrok / frp / cpolar | 本地调试时 curl 模拟 | MVP |

### 技术组件

| 组件 | 用途 | 版本 |
|:---|:---|:---:|
| FastAPI | Web 框架 | 0.115+ |
| SQLAlchemy 2.0 | ORM | 2.0+ |
| asyncpg | PostgreSQL 异步驱动 | - |
| Redis (redis-py) | 缓存、任务队列 | 5.0+ |
| httpx | 异步 HTTP 客户端（调飞书API） | - |
| APScheduler | 定时任务（周报/月报） | - |
| pg_trgm | PostgreSQL 模糊搜索扩展 | - |

### 部署架构（MVP）

```
[飞书] ←→ [公网隧道(ngrok)] ←→ [FastAPI App] ←→ [PostgreSQL + Redis]
                                        ↑
[Git Webhook] ←─────────────────────────┘
```

- 单机部署：1C2G 云服务器 + Docker
- 数据库：PostgreSQL 15（同机部署或 RDS）
- Redis：缓存+轻量任务队列
- 隧道：ngrok 固定域名（付费版，月约$5）

### MVP 实施范围（P0 清单）

| 编号 | 功能 | 模块 |
|:---:|:---|:---:|
| P0-1 | 项目 CRUD + 飞书看板任务同步 | 项目管理 |
| P0-2 | Git Webhook 接收 + 事件存储 | 系统基础 |
| P0-3 | 原子能力 CRUD + 自然语言搜索（关键词） | 能力管理 |
| P0-4 | Git commit 扫描 + 能力草稿生成 | 能力管理 |
| P0-5 | 能力推荐 + 飞书消息推送 | 能力管理 |
| P0-6 | 反馈记录（硬编码有用/无用按钮） | 能力管理 |
| P0-7 | 操作日志 + 审计 | 系统基础 |
| P0-8 | 飞书身份验证中间件 | 系统基础 |
