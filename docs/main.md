# AI对话助手设计文档（v1.0）

## 1. 项目概述

**项目名称**：AI对话助手（AI Chat Assistant）  
**用途**：一个全栈AI对话框架，提供类Gemini/Grok的聊天体验，支持上下文记忆、Markdown渲染、附件处理，并具备可扩展的Agent路由机制。核心是“智能主管Agent + 可插拔专业Agent”的架构，主Agent负责意图识别与任务分配，专业Agent负责具体垂直任务执行。

**核心特性**
- 前端：现代Web聊天界面，支持Markdown渲染、深色/浅色主题切换
- 后端：对话历史管理、上下文记忆、附件临时上传处理、意图识别路由、可自定义接入多种专业Agent
- 扩展性：不依赖LangChain/CrewAI等框架，通过原生LLM函数调用或自定义路由表实现Agent调度

## 2. 功能需求

### 2.1 前端功能
- **布局**
  - 左侧侧边栏：对话历史列表（支持新建、删除、搜索历史标题）
  - 中间主区域：对话消息流（参考Gemini + Grok风格，上方标题栏显示当前对话主题，下方输入框）
  - 右侧可选面板：预留（未来可扩展Agent状态、附件预览等）
- **消息渲染**
  - AI回复支持完整Markdown渲染（代码高亮、表格、LaTeX、列表等）
  - 支持流式输出（streaming）
- **主题切换**
  - 深色/浅色模式全局切换（持久化到localStorage）
- **附件上传**
  - 支持拖拽或点击上传图片、视频、Excel、PDF等多种格式
  - 上传后立即显示预览缩略图
  - 上传文件通过后端接口转发至temp目录
- **交互**
  - 新建对话、清空当前对话
  - 输入框支持Enter发送、Shift+Enter换行

### 2.2 后端功能
- **对话管理**
  - 新建对话、删除对话、列出历史对话
  - 每条对话保存完整上下文消息历史（user/assistant/system）
  - 支持设置对话标题（可由LLM自动生成）
- **上下文记忆**
  - 单对话内完整上下文传递给LLM
  - 可配置最大上下文长度（token截断策略）
- **消息输出**
  - AI回复统一为Markdown格式
  - 支持streaming响应（SSE或WebSocket）
- **意图识别与Agent路由**
  - 主Agent（Supervisor）接收用户消息后，先进行意图识别
  - 根据识别结果，决定：
    - 直接回复
    - 调用某个已注册的专业Agent执行任务
    - 返回工具调用结果后再生成最终回复
  - 支持动态注册Agent（通过配置文件或插件机制）
  - 示例：用户输入“分析BTC市场情绪”，主Agent识别为金融分析意图 → 调用FinancialAnalysisAgent → Agent执行后返回结果 → 主Agent整合为最终Markdown回复
- **附件处理**
  - 接收前端上传文件，保存至`temp/`目录（带唯一ID命名）
  - 支持多模态LLM直接处理图片/视频
  - 对于Excel/PDF，使用对应库（pandas/openpyxl/PyPDF2/pdfplumber等）提取内容后交给LLM或专业Agent
  - 任务处理完成后自动删除temp目录下对应文件
- **安全与清理**
  - 上传文件大小限制、类型白名单
  - 定时清理过期temp文件（可选）

## 3. 系统架构

```
前端 (React)  <--WebSocket/SSE + REST-->  后端 (FastAPI)
                                           |
                                           ├── 主Agent（Supervisor）
                                           │    ├── 意图识别（LLM Prompt / Function Calling）
                                           │    └── 路由到专业Agent
                                           ├── 专业Agent集合（可插拔）
                                           │    ├── FinancialAnalysisAgent
                                           │    ├── DocumentAnalysisAgent
                                           │    └── ...
                                           ├── 附件处理服务
                                           └── 数据库（MongoDB / SQLite）
```

- **通信方式**
  - 聊天流式响应：WebSocket 或 SSE
  - 其他操作（历史列表、上传文件）：REST API
- **Agent调度机制**（不使用禁用框架）
  - 方案一：OpenAI/Anthropic原生Function Calling（定义工具函数对应不同Agent）
  - 方案二：自定义路由表 + Prompt分类（轻量级，适合多模型兼容）

## 4. 技术栈

**前端**
- Next 14 + TypeScript
- UI库：Tailwind CSS + shadcn/ui（组件美观、易自定义主题）
- Markdown渲染：react-markdown + remark-gfm + rehype-raw
- 状态管理：Zustand 或 Context API
- 流式响应：WebSocket客户端库
- 主题切换：tailwind dark mode + next-themes风格

**后端**
- Web框架：FastAPI（异步、高性能、自动OpenAPI文档）
- 配置管理：pydantic-settings
- 数据库：MongoDB（灵活存储对话历史）或 SQLite（轻量部署）
- LLM调用：通用封装，支持OpenAI、Anthropic、Groq、DeepSeek、Qwen等
- 附件处理：
  - 图片/视频：直接传URL给多模态LLM
  - Excel：pandas / openpyxl
  - PDF：PyPDF2 + pdfplumber
- 文件上传：FastAPI内置上传 + tempfile管理
- 日志：structlog
- 部署：Docker + Uvicorn/Gunicorn

**禁止技术**：LangChain、CrewAI、LlamaIndex等任何类似Agent框架

## 5. API 接口概览（后端）

| 方法   | 路径                        | 功能                     |
|--------|-----------------------------|--------------------------|
| GET    | /conversations              | 获取对话历史列表         |
| POST   | /conversations              | 新建对话                 |
| DELETE | /conversations/{id}         | 删除对话                 |
| GET    | /conversations/{id}/messages| 获取对话消息             |
| POST   | /chat/{conv_id}             | 发送消息（支持streaming）|
| POST   | /upload                     | 上传附件（返回文件ID）   |

## 6. 开发计划（建议）

1. 搭建FastAPI基础结构 + MongoDB对话存储
2. 实现主Agent意图识别与简单路由
3. 前端React基础布局 + Markdown渲染
4. 接入WebSocket流式聊天
5. 实现附件上传与temp清理
6. 开发示例专业Agent（金融分析）
7. 主题切换与UI美化
8. 测试与部署

## 项目结构

```text
ai_chat_assistant/
├── frontend/                     # React 前端代码
│   ├── src/
│   │   ├── app/                  # 路由与布局
│   │   ├── components/           # UI组件（ChatMessage, Sidebar, ThemeToggle等）
│   │   ├── lib/                  # API客户端、WebSocket工具
│   │   ├── stores/               # Zustand状态管理
│   │   └── main.tsx
│   ├── public/
│   ├── tailwind.config.js
│   └── package.json
│
├── backend/                      # FastAPI 后端代码
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py               # FastAPI app 入口
│   │   ├── config.py             # 配置 (pydantic-settings)
│   │   ├── api/                  # API路由
│   │   │   ├── chat.py           # 聊天接口
│   │   │   ├── conversations.py  # 对话管理
│   │   │   └── upload.py         # 文件上传
│   │   ├── core/                 # 核心服务
│   │   │   ├── supervisor.py     # 主Agent（意图识别 + 路由）
│   │   │   ├── llm_client.py     # 统一LLM调用封装
│   │   │   └── streaming.py      # 流式响应工具
│   │   ├── agents/               # 可插拔专业Agent
│   │   │   ├── __init__.py
│   │   │   ├── base.py           # Agent基类
│   │   │   └── financial.py      # 示例：金融分析Agent
│   │   ├── services/             # 业务服务
│   │   │   ├── attachment.py     # 附件处理与temp清理
│   │   │   └── document.py       # PDF/Excel解析
│   │   ├── models/               # Pydantic数据模型
│   │   │   └── conversation.py
│   │   ├── db/                   # 数据库操作
│   │   │   └── mongo.py
│   │   └── utils/
│   │       ├── logger.py
│   │       └── temp_manager.py   # temp目录管理
│   ├── temp/                     # 临时上传文件目录（git ignore）
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── .env.example
│
├── docs/
│   └── v1.0.md                   # 本文档
├── docker-compose.yml            # 前后端 + MongoDB 一键部署
├── .gitignore
└── README.md
```