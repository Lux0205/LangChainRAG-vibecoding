# LangChain RAG 企业级电商知识库问答系统

基于 LangChain 框架的 RAG（检索增强生成）企业级知识库问答系统，面向电商平台场景，支持商品知识智能问答。

## 功能特性

- 🔐 **用户认证**：注册/登录/修改密码，JWT Token认证
- 👥 **多用户多会话**：每个用户独立会话，历史对话持久化
- 🤖 **智能问答**：基于RAG的商品知识问答，回答附带引用来源
- 📚 **知识库管理**：管理员上传/删除知识文档（PDF/DOCX/TXT/CSV）
- 🔍 **混合检索**：向量检索 + BM25关键词检索 + RRF融合
- ⚡ **流式输出**：SSE流式响应，打字机效果
- 🔄 **多模型切换**：支持通义千问/智谱GLM切换
- 🛡️ **权限控制**：RBAC角色权限，管理员/用户分离

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python + FastAPI + LangChain |
| LLM | 通义千问 / 智谱GLM |
| 向量库 | Milvus 2.x |
| 数据库 | MySQL 8.0 |
| 缓存 | Redis |
| 前端 | Vue3 + Element Plus + Vite |
| 认证 | JWT (python-jose) |

## 快速开始

### 前置依赖

- Python 3.10+
- Node.js 18+
- MySQL 8.0
- Redis
- Milvus 2.x（单机版）

### 安装步骤

#### 1. 创建MySQL数据库

```sql
CREATE DATABASE rag_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

#### 2. 配置环境变量

```bash
cd backend
cp .env.example .env
# 编辑 .env 文件，填入API Key和数据库密码
```

#### 3. 一键安装

```bash
# Windows
scripts\setup_env.bat
```

#### 4. 启动系统

```bash
# Windows
scripts\start_all.bat
```

### 访问系统

- 前端: http://localhost:5173
- 后端API文档: http://localhost:8000/docs
- 默认管理员: `admin` / `123456`

## 项目结构

```
├── backend/          # Python后端
│   ├── app/
│   │   ├── api/      # API路由
│   │   ├── models/   # 数据模型
│   │   ├── services/ # 业务逻辑
│   │   ├── rag/      # RAG流水线
│   │   ├── middleware/ # 中间件
│   │   └── utils/    # 工具函数
│   └── init_data.py  # 初始化数据
├── frontend/         # Vue3前端
│   └── src/
│       ├── views/    # 页面组件
│       ├── stores/   # 状态管理
│       ├── api/      # API请求
│       └── router/   # 路由配置
├── scripts/          # 部署脚本
├── milvus/           # Milvus配置
└── docs/             # 文档
```

## RAG流水线

```
用户提问 → 问题预处理 → 向量化 → 混合检索(向量+BM25) → 重排序 → Prompt组装 → LLM生成 → 引用溯源
```

## 知识库支持格式

- PDF (.pdf)
- Word (.docx)
- 文本 (.txt)
- CSV (.csv)

## 许可

MIT License
