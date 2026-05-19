# AI 测试平台

基于 LLM 的自动化测试平台，支持自然语言生成 Playwright 测试脚本并执行。

## 技术栈

| 层 | 技术 |
|---|------|
| 前端 | Vue 3 + Ant Design Vue + Vite |
| 后端 | Python 3.11 + FastAPI |
| 数据库 | MySQL 8.0 + Redis 6 |
| 测试执行 | Playwright (Chromium) |
| LLM | OpenAI 兼容接口（MiniMax、DeepSeek、Kimi 等） |

## 功能

- **5种测试用例生成方式**：Swagger上传、页面URL解析、PRD文档、手动编写、导入Excel/CSV/JSON
- **自然语言生成脚本**：LLM 根据测试用例自动生成 Playwright 代码
- **自动执行测试**：Playwright 执行脚本，自动截图记录
- **测试结果管理**：历史记录、截图查看、通过率统计
- **场景/功能管理**：按场景组织测试用例，按功能分类

## 目录结构

```
ai-test-platform/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口
│   │   ├── models/              # 数据库模型
│   │   ├── routers/             # API 路由
│   │   │   ├── test_cases.py    # 测试用例 CRUD
│   │   │   ├── executions.py    # 测试执行
│   │   │   ├── generation.py    # 脚本生成
│   │   │   ├── generate_cases.py # 用例生成（URL/PRD/文件）
│   │   │   ├── suites.py        # 场景管理
│   │   │   ├── functions.py     # 功能管理
│   │   │   ├── documents.py     # 文档管理
│   │   │   └── model_configs.py # LLM 配置
│   │   └── services/
│   │       ├── llm_service.py   # LLM 调用封装
│   │       └── executor.py      # Playwright 执行器
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── views/               # 页面组件
│   │   ├── router/              # 路由配置
│   │   ├── api/                 # API 调用
│   │   └── store/               # Pinia 状态管理
│   └── package.json
├── screenshots/                 # 测试截图（自动创建）
├── uploads/                     # 上传文件（自动创建）
└── README.md
```

## 部署

### 环境要求

- Python 3.11+
- Node.js 18+
- Docker（运行 MySQL 8.0）
- Redis 6

### 1. 克隆项目

```bash
git clone <repo-url>
cd ai-test-platform
```

### 2. 后端部署

```bash
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install chromium

# 创建数据库（Docker MySQL）
docker exec mysql8 mysql -uroot -proot -e "CREATE DATABASE IF NOT EXISTS ai_test_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 启动后端（开发模式）
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. 前端部署

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 4. 访问

- 前端：http://localhost:3000
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

### 5. 配置 LLM

首次使用需要在「系统设置」页面配置 LLM 模型：

| 字段 | 示例 |
|------|------|
| 名称 | MiniMax |
| Base URL | https://api.minimax.chat/v1 |
| Model | MiniMax-M2.7-highspeed |
| API Key | 你的 API Key |

支持任何 OpenAI 兼容接口。

## API 概览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET/POST | /api/test_cases | 测试用例 CRUD |
| POST | /api/generation/generate-script | 生成测试脚本 |
| POST | /api/generation/execute | 执行测试脚本 |
| GET | /api/executions | 执行记录列表 |
| GET | /api/executions/{id} | 执行详情（含截图） |
| POST | /api/generate/from-url | 从 URL 生成用例 |
| POST | /api/generate/from-prd | 从 PRD 文档生成用例 |
| POST | /api/generate/from-file | 从文件生成用例 |
| GET/POST | /api/suites | 场景管理 |
| GET/POST | /api/functions | 功能管理 |
| GET/POST | /api/documents | 文档管理 |
| GET/POST | /api/model_configs | LLM 配置 |

## 使用流程

1. **配置 LLM** → 系统设置 → 添加模型配置
2. **创建功能** → 功能管理 → 新建功能模块
3. **生成用例** → 测试用例 → 选择生成方式（URL/PRD/文件）
4. **创建场景** → 场景管理 → 新建场景 → 添加功能
5. **生成脚本** → 场景详情 → 生成脚本
6. **执行测试** → 场景详情 → 执行测试 → 查看截图结果

## 数据库表

| 表名 | 说明 |
|------|------|
| test_cases | 测试用例 |
| test_case_history | 用例修改历史 |
| test_executions | 执行记录 |
| test_screenshots | 截图记录 |
| uploaded_documents | 上传文档 |
| model_configs | LLM 模型配置 |
| test_suites | 测试场景 |
| test_functions | 功能模块 |

## 注意事项

- 截图存储在 `screenshots/` 目录，按执行ID分文件夹
- 上传文件存储在 `uploads/` 目录
- LLM 生成脚本质量取决于模型能力，推荐使用 Qwen2.5-Coder 或 DeepSeek-Coder
- Playwright 执行需要 Chromium 浏览器，首次使用需 `playwright install chromium`
