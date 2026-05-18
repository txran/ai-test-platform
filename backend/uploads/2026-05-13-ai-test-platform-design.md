# AI测试平台 - 概要设计文档

**创建日期：** 2026-05-13
**版本：** v1.0
**状态：** 已批准
**关联文档：** [需求文档](./2026-05-13-ai-test-platform-requirements.md)

---

## 1. 技术选型

| 层 | 技术栈 | 说明 |
|---|---|---|
| 前端 | Vue3 + Ant Design Vue | SPA，中文UI |
| 后端 | Python + FastAPI | 异步API框架 |
| 数据库 | MySQL 8.0 | 结构化数据存储 |
| 缓存 | Redis 6 | 缓存、任务队列 |
| 浏览器自动化 | Playwright (Python) | 无头/有头模式 |
| 截图存储 | 本地文件系统 | 按执行ID组织 |

---

## 2. 系统架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      用户浏览器                               │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP
┌─────────────────────▼───────────────────────────────────────┐
│                 Vue3 前端 (3000端口)                          │
│        Ant Design Vue + Vue Router + Pinia                   │
└─────────────────────┬───────────────────────────────────────┘
                      │ REST API
┌─────────────────────▼───────────────────────────────────────┐
│                FastAPI 后端 (8000端口)                        │
│   ┌──────────┬──────────┬──────────┬──────────┬──────────┐  │
│   │ 测试用例  │ 测试执行  │ 文档管理  │ 模型配置  │ 生成服务  │  │
│   └──────────┴──────────┴──────────┴──────────┴──────────┘  │
└─────────┬───────────────────────────────────────────────────┘
          │                           │
          ▼                           ▼
┌──────────────────┐        ┌──────────────────┐
│   MySQL (18306)  │        │   LLM API        │
│   ai_test_platform│       │ (OpenAI兼容格式)  │
└──────────────────┘        └──────────────────┘
          │
          ▼
┌──────────────────┐
│  本地文件系统      │
│  /uploads        │
│  /screenshots    │
└──────────────────┘
```

### 2.2 前端模块

| 模块 | 页面路径 | 功能 |
|------|---------|------|
| 测试用例管理 | /test-cases | 列表、筛选、批量操作 |
| 测试用例新建 | /test-cases/new | 5种生成方式 |
| 测试用例详情 | /test-cases/:id | 详情、脚本、执行历史 |
| 执行记录 | /executions | 执行历史列表 |
| 执行详情 | /executions/:id | 截图、结果、错误 |
| 文档管理 | /documents | 文档上传、列表 |
| 设置 | /settings | 模型配置 |

### 2.3 后端模块

| 模块 | 路由前缀 | 功能 |
|------|---------|------|
| test_cases | /api/test-cases | 测试用例CRUD |
| executions | /api/executions | 测试执行、结果查询 |
| documents | /api/documents | 文档上传、管理 |
| model_configs | /api/model-configs | 模型配置CRUD |
| generation | /api/generate | 测试用例生成（5种方式） |

---

## 3. 数据库设计

### 3.1 ER图

```
┌─────────────────┐       ┌─────────────────┐
│   test_cases    │       │  test_scripts   │
├─────────────────┤       ├─────────────────┤
│ id (PK)        │◄──┐   │ id (PK)        │
│ name           │   │   │ test_case_id (FK)│──┐
│ description    │   │   │ version        │  │
│ group_id       │   │   │ script_content │  │
│ tags           │   │   │ is_current     │  │
│ status         │   │   │ created_at     │  │
│ source_type    │   │   └─────────────────┘  │
│ source_doc_id  │   │                         │
│ current_version│   │   ┌─────────────────┐  │
│ created_at     │   │   │test_executions  │  │
│ updated_at     │   │   ├─────────────────┤  │
└─────────────────┘   │   │ id (PK)        │  │
                       └───┤ test_case_id(FK)│  │
                           │ script_id (FK) │◄─┘
                           │ status         │
                           │ start_time     │
                           │ end_time       │
                           │ duration       │
                           │ error_message  │
                           └─────────────────┘
                                    │
                                    ▼
                           ┌─────────────────┐
                           │test_screenshots │
                           ├─────────────────┤
                           │ id (PK)        │
                           │ execution_id(FK)│
                           │ step_number    │
                           │ step_desc      │
                           │ screenshot_path│
                           └─────────────────┘
```

### 3.2 表结构

#### test_cases（测试用例表）
```sql
id              INT PRIMARY KEY AUTO_INCREMENT
name            VARCHAR(255) NOT NULL
description     TEXT
group_id        INT
tags            JSON
status          ENUM('active', 'inactive', 'draft')
source_type     ENUM('swagger', 'url', 'prd', 'manual', 'import')
source_document_id INT
current_version INT DEFAULT 1
created_at      TIMESTAMP
updated_at      TIMESTAMP
```

#### test_scripts（测试脚本表）
```sql
id              INT PRIMARY KEY AUTO_INCREMENT
test_case_id    INT NOT NULL (FK → test_cases.id)
version         INT NOT NULL
script_content  TEXT NOT NULL
is_current      BOOLEAN DEFAULT FALSE
created_at      TIMESTAMP
```

#### test_executions（测试执行记录表）
```sql
id              INT PRIMARY KEY AUTO_INCREMENT
test_case_id    INT NOT NULL (FK → test_cases.id)
script_id       INT NOT NULL (FK → test_scripts.id)
status          ENUM('pending', 'running', 'passed', 'failed', 'error')
start_time      TIMESTAMP
end_time        TIMESTAMP
duration        INT
error_message   TEXT
llm_response    TEXT
created_at      TIMESTAMP
```

#### test_screenshots（测试截图表）
```sql
id              INT PRIMARY KEY AUTO_INCREMENT
execution_id    INT NOT NULL (FK → test_executions.id)
step_number     INT NOT NULL
step_description TEXT
screenshot_path VARCHAR(500)
created_at      TIMESTAMP
```

#### uploaded_documents（上传文档表）
```sql
id              INT PRIMARY KEY AUTO_INCREMENT
name            VARCHAR(255) NOT NULL
file_type       ENUM('swagger', 'prd', 'excel', 'csv', 'json')
file_path       VARCHAR(500)
file_size       INT
created_at      TIMESTAMP
```

#### test_case_history（测试用例修改历史表）
```sql
id              INT PRIMARY KEY AUTO_INCREMENT
test_case_id    INT NOT NULL (FK → test_cases.id)
version         INT NOT NULL
change_type     ENUM('create', 'update', 'delete')
change_description TEXT
changed_fields  JSON
old_value       JSON
new_value       JSON
created_at      TIMESTAMP
```

#### model_configs（模型配置表）
```sql
id              INT PRIMARY KEY AUTO_INCREMENT
name            VARCHAR(255) NOT NULL
provider        VARCHAR(100)
base_url        VARCHAR(500)
api_key         VARCHAR(500)
model_name      VARCHAR(100)
is_default      BOOLEAN DEFAULT FALSE
created_at      TIMESTAMP
```

---

## 4. API设计

### 4.1 测试用例管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/test-cases | 获取列表（支持分页、筛选） |
| POST | /api/test-cases | 创建测试用例 |
| GET | /api/test-cases/{id} | 获取详情 |
| PUT | /api/test-cases/{id} | 更新测试用例 |
| DELETE | /api/test-cases/{id} | 删除测试用例 |
| GET | /api/test-cases/{id}/history | 获取修改历史 |

### 4.2 测试脚本管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/test-cases/{id}/scripts | 获取脚本列表 |
| POST | /api/test-cases/{id}/scripts | 创建脚本 |
| GET | /api/scripts/{id} | 获取脚本详情 |
| PUT | /api/scripts/{id} | 更新脚本 |
| DELETE | /api/scripts/{id} | 删除脚本 |

### 4.3 测试用例生成

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/generate/from-swagger | 从Swagger生成 |
| POST | /api/generate/from-url | 从页面URL生成 |
| POST | /api/generate/from-prd | 从需求文档生成 |
| POST | /api/generate/manual | 手动编写（直接保存） |

### 4.4 文档管理

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/documents/upload | 上传文档 |
| GET | /api/documents | 获取文档列表 |
| DELETE | /api/documents/{id} | 删除文档 |

### 4.5 测试执行

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/executions/run | 执行测试用例 |
| GET | /api/executions/{id} | 获取执行结果 |
| GET | /api/test-cases/{id}/executions | 获取执行历史 |

### 4.6 截图管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/executions/{id}/screenshots | 获取执行截图 |

### 4.7 模型配置

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/model-configs | 获取模型配置列表 |
| POST | /api/model-configs | 创建模型配置 |
| PUT | /api/model-configs/{id} | 更新模型配置 |
| DELETE | /api/model-configs/{id} | 删除模型配置 |

---

## 5. 目录结构

```
ai-test-platform/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI入口
│   │   ├── models/
│   │   │   ├── database.py      # 数据库连接
│   │   │   └── models.py        # SQLAlchemy模型
│   │   ├── routers/
│   │   │   ├── test_cases.py    # 测试用例API
│   │   │   ├── executions.py    # 执行API
│   │   │   ├── documents.py     # 文档API
│   │   │   ├── model_configs.py # 模型配置API
│   │   │   └── generation.py    # 生成API
│   │   └── services/
│   │       ├── llm_service.py   # LLM调用服务
│   │       └── executor.py      # Playwright执行器
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── views/
│   │   │   ├── TestCases.vue
│   │   │   ├── TestCaseNew.vue
│   │   │   ├── TestCaseDetail.vue
│   │   │   ├── Executions.vue
│   │   │   ├── ExecutionDetail.vue
│   │   │   ├── Documents.vue
│   │   │   └── Settings.vue
│   │   ├── api/index.js
│   │   ├── router/index.js
│   │   └── main.js
│   └── package.json
├── uploads/                    # 上传文件目录
└── screenshots/               # 截图存储目录
```

---

## 6. 技术细节

### 6.1 LLM调用
- 支持OpenAI兼容格式
- 通过base_url和api_key配置不同模型
- 模型配置存储在model_configs表

### 6.2 Playwright执行
- 使用Playwright for Python
- 支持无头模式（headless）和有头模式（headed）
- 每步操作自动截图

### 6.3 截图存储
- 本地文件系统
- 路径格式：`/screenshots/{execution_id}/{step_number}.png`

### 6.4 版本管理
- 测试用例版本：current_version字段
- 脚本版本：test_scripts.version字段
- 修改历史：test_case_history表记录每次变更

---

## 7. 部署架构

```
┌─────────────────────────────────────────────┐
│              本地主机 (GodOfWar)              │
│                                             │
│  ┌──────────────┐    ┌──────────────┐      │
│  │   Vue3 前端   │    │  FastAPI 后端 │      │
│  │   :3000      │    │   :8000      │      │
│  └──────────────┘    └──────────────┘      │
│                              │              │
│         ┌────────────────────┼──────┐      │
│         ▼                    ▼      ▼      │
│  ┌──────────────┐    ┌──────────────┐      │
│  │ MySQL Docker │    │ Redis Docker │      │
│  │   :18306     │    │   :18379     │      │
│  └──────────────┘    └──────────────┘      │
└─────────────────────────────────────────────┘
```

---

## 8. 开发计划

### MVP（4-6天）

| 阶段 | 天数 | 内容 |
|------|------|------|
| 后端开发 | 1-2天 | 数据库表、API、LLM服务、执行器 |
| 前端开发 | 3-4天 | Vue页面、API对接 |
| 联调测试 | 5-6天 | 前后端联调、Bug修复 |

### 后续迭代
- 文档管理功能完善
- 5种生成方式完善
- 版本对比功能
- UI变化检测
- 批量/并发执行
