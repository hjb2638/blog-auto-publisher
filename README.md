# 博客自动发布系统 / Blog Auto-Publishing System

[![Python](https://img.shields.io/badge/Python-3.12+-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61dafb)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-blue)](https://www.typescriptlang.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791)](https://www.postgresql.org/)

---

## 中文文档

### 项目简介

基于 AI 的博客内容自动生成与发布平台。输入主题 → LLM 生成大纲 → 人工审核 → LLM 撰写全文 → 审核 → 自动搜索配图 → 一键发布到 WordPress。

**实际运行网站：** [www.bojinhu.xyz](https://www.bojinhu.xyz)

### 核心功能

- **四阶段流水线** — 大纲 → 内容 → 配图 → 发布，每阶段可人工审核
- **自动发布模式** — 跳过所有审核，全程自动生成并发布
- **LLM 驱动** — DeepSeek (Qwen3-Next-80B-A3B MoE)，OpenAI 兼容 API，81K 上下文
- **实时进度推送** — SSE 流式推送每个生成阶段的进度
- **智能配图** — LLM 生成搜索关键词，自动从 Unsplash 获取相关图片
- **WordPress 集成** — 一键发布，支持草稿/发布状态控制

### 技术栈

| 层级 | 技术 |
|---|---|
| 后端框架 | FastAPI + SQLAlchemy (async) + Pydantic v2 |
| 前端框架 | React 18 + TypeScript + Tailwind CSS + React Query |
| 数据库 | PostgreSQL 16 (asyncpg 驱动) |
| 大模型 | DeepSeek (OpenAI 兼容 API) |
| 图片 API | Unsplash |
| 开发服务器 | Vite + Uvicorn |

### 架构

```
用户 → React 前端 → FastAPI 后端 → LLM API (大纲/内容生成)
                                 → Unsplash API (图片搜索)
                                 → WordPress REST API (发布)
                                 → PostgreSQL (状态持久化)
```

### 状态机（14 个状态）

```
draft → outline_generating → outline_ready → outline_approved
      → content_generating → content_ready → content_approved
      → image_searching → images_ready → final_approved
      → publishing → published

failed   — 从任意生成状态可恢复
cancelled — 从任意非终态可取消
```

### 项目结构

```
blog_project/
├── docker-compose.yml
├── .env.example
├── README.md
├── backend/
│   ├── app/
│   │   ├── core/          # 配置、数据库、依赖注入
│   │   ├── models/        # SQLAlchemy ORM 模型
│   │   ├── schemas/       # Pydantic 请求/响应模型
│   │   ├── routers/       # FastAPI 路由 + SSE 流
│   │   ├── services/      # LLM、大纲、内容、图片、WordPress 服务
│   │   ├── prompts/       # LLM prompt 模板
│   │   └── utils/         # 日志、重试、HTML 清洗
│   └── tests/
└── frontend/
    └── src/
        ├── components/    # UI 组件
        ├── hooks/         # React Query hooks
        ├── pages/         # 路由页面
        └── api/           # Axios 客户端
```

### 快速启动

#### 环境要求

- Python 3.12+, Node.js 20+, PostgreSQL 16
- WordPress 站点（需 Application Password）
- Unsplash API Access Key

#### 1. 安装依赖

```bash
# 后端
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 前端
cd frontend
npm install
```

#### 2. 配置环境变量

复制 `.env.example` 为 `.env`，填写配置：

```env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5433/blog_db
LLM_BASE_URL=http://your-llm-api/v1
LLM_MODEL=deepseek
UNSPLASH_ACCESS_KEY=your_unsplash_key
WP_API_URL=https://your-site.com/index.php/wp-json
WP_USERNAME=your_username
WP_APP_PASSWORD=your_app_password
```

#### 3. 启动

```bash
# 启动后端 (端口 8000)
cd backend
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# 启动前端 (端口 5173)
cd frontend
npm run dev
```

#### 4. Docker 启动（可选）

```bash
docker compose up -d
```

### API 接口

| 方法 | 路径 | 说明 |
|---|---|---|
| `POST` | `/api/v1/articles` | 创建文章 `{topic, requirements?, mode}` |
| `GET` | `/api/v1/articles` | 文章列表（分页 + 状态筛选） |
| `GET` | `/api/v1/articles/{id}` | 文章详情（含大纲/内容/图片） |
| `GET` | `/api/v1/articles/{id}/status` | 轻量状态查询 |
| `GET` | `/api/v1/articles/{id}/stream` | SSE 进度推送 |
| `POST` | `/api/v1/articles/{id}/approve-outline` | 审核大纲 |
| `POST` | `/api/v1/articles/{id}/approve-content` | 审核内容 |
| `POST` | `/api/v1/articles/{id}/approve-final` | 最终审核 |
| `POST` | `/api/v1/articles/{id}/publish` | 发布到 WordPress |
| `POST` | `/api/v1/articles/{id}/regenerate` | 重新生成 |
| `DELETE` | `/api/v1/articles/{id}` | 删除文章 |
| `GET` | `/api/v1/health` | 健康检查 |

### 界面截图

#### 文章列表首页

![首页](docs/images/homepage.png)

#### 创建文章

![创建文章](docs/images/create-article.png)

#### 大纲审核

![大纲审核](docs/images/outline-review.png)

#### 发布成功

![发布成功](docs/images/published.png)

### 测试

```bash
cd backend
pytest tests/ -v
```

全部 28 个测试覆盖：文章 CRUD、状态机转换（11 种场景）、LLM 服务（5 个）、WordPress 服务（4 个）。

### 发布模式

- **手动模式 (Manual)** — 每个阶段需人工审核确认，适合精细控制内容质量
- **自动模式 (Auto)** — 输入主题后全程自动生成并发布，无需人工干预

---

## English Documentation

### Overview

AI-powered blog content generation and publishing platform. Enter a topic → LLM generates an outline → review → LLM writes the full article → review → images are auto-searched → one-click publish to WordPress.

**Live Site:** [www.bojinhu.xyz](https://www.bojinhu.xyz)

### Features

- **4-Stage Pipeline** — Outline → Content → Images → Publish, with manual review at each step
- **Auto-Publish Mode** — Skip all reviews, generate and publish fully automatically
- **LLM-Powered** — DeepSeek (Qwen3-Next-80B-A3B MoE) via OpenAI-compatible API, 81K context
- **Real-Time Progress** — SSE streaming for each generation stage
- **Smart Image Search** — LLM generates keywords, automatically fetches relevant images from Unsplash
- **WordPress Integration** — One-click publish with draft/publish status control

### Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI + SQLAlchemy (async) + Pydantic v2 |
| Frontend | React 18 + TypeScript + Tailwind CSS + React Query |
| Database | PostgreSQL 16 (asyncpg) |
| LLM | DeepSeek (OpenAI-compatible API) |
| Image API | Unsplash |
| Dev Server | Vite + Uvicorn |

### Architecture

```
User → React Frontend → FastAPI Backend → LLM API (outline/content)
                                     → Unsplash API (images)
                                     → WordPress REST API (publish)
                                     → PostgreSQL (state)
```

### State Machine (14 States)

```
draft → outline_generating → outline_ready → outline_approved
      → content_generating → content_ready → content_approved
      → image_searching → images_ready → final_approved
      → publishing → published

failed    — recoverable from any generating state
cancelled — terminal, from any non-terminal state
```

### Project Structure

```
blog_project/
├── docker-compose.yml
├── .env.example
├── README.md
├── backend/
│   ├── app/
│   │   ├── core/          # config, database, DI
│   │   ├── models/        # SQLAlchemy ORM
│   │   ├── schemas/       # Pydantic models
│   │   ├── routers/       # FastAPI endpoints + SSE
│   │   ├── services/      # LLM, outline, content, image, WP
│   │   ├── prompts/       # prompt templates
│   │   └── utils/         # logging, retry, sanitizer
│   └── tests/
└── frontend/
    └── src/
        ├── components/    # UI components
        ├── hooks/         # React Query hooks
        ├── pages/         # route pages
        └── api/           # Axios client
```

### Quick Start

#### Prerequisites

- Python 3.12+, Node.js 20+, PostgreSQL 16
- WordPress site with Application Password
- Unsplash API Access Key

#### 1. Install Dependencies

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

#### 2. Configure

Copy `.env.example` to `.env`:

```env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5433/blog_db
LLM_BASE_URL=http://your-llm-api/v1
LLM_MODEL=deepseek
UNSPLASH_ACCESS_KEY=your_unsplash_key
WP_API_URL=https://your-site.com/index.php/wp-json
WP_USERNAME=your_username
WP_APP_PASSWORD=your_app_password
```

#### 3. Run

```bash
# Backend (port 8000)
cd backend
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Frontend (port 5173)
cd frontend
npm run dev
```

#### 4. Docker

```bash
docker compose up -d
```

### API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/articles` | Create article `{topic, requirements?, mode}` |
| `GET` | `/api/v1/articles` | List articles (pagination + status filter) |
| `GET` | `/api/v1/articles/{id}` | Full article detail |
| `GET` | `/api/v1/articles/{id}/status` | Lightweight status poll |
| `GET` | `/api/v1/articles/{id}/stream` | SSE progress events |
| `POST` | `/api/v1/articles/{id}/approve-outline` | Confirm outline |
| `POST` | `/api/v1/articles/{id}/approve-content` | Confirm content |
| `POST` | `/api/v1/articles/{id}/approve-final` | Final approval |
| `POST` | `/api/v1/articles/{id}/publish` | Publish to WordPress |
| `POST` | `/api/v1/articles/{id}/regenerate` | Regenerate |
| `DELETE` | `/api/v1/articles/{id}` | Delete article |
| `GET` | `/api/v1/health` | Health check |

### Screenshots

See Chinese section above for screenshots (same images in `docs/images/`).

### Testing

```bash
cd backend
pytest tests/ -v
```

28 tests: article CRUD, state machine (11 cases), LLM service (5), WordPress service (4).

### Modes

- **Manual** — Review and approve at each stage
- **Auto** — Fully automated generation and publishing
