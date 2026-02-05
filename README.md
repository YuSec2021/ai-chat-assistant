# AI Chat Assistant (v1.1)

A full-stack AI chat assistant with agent routing, streaming responses, and file attachment support.

## Features

- **Modern Next.js Frontend**: Built with Next.js 14 (App Router), TypeScript, and Tailwind CSS
- **Agent Routing**: Smart supervisor agent routes requests to specialized agents
- **Streaming Responses**: Real-time chat via WebSocket
- **File Attachments**: Upload images, PDFs, Excel files for analysis
- **Markdown Rendering**: Rich text formatting with code highlighting
- **Dark/Light Mode**: Theme switching with next-themes
- **Conversation Management**: Create, delete, and search conversations

## Tech Stack

### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first CSS
- **shadcn/ui** - Reusable components
- **next-themes** - Theme management
- **Zustand** - State management
- **react-markdown** - Markdown rendering with syntax highlighting

### Backend
- **FastAPI** - Modern async web framework
- **MongoDB** - Flexible document storage
- **OpenAI/Anthropic APIs** - LLM integration
- **Python 3.11+** with uv package manager

## Quick Start

### Prerequisites

- Python 3.11+
- uv (Python package manager)
- Node.js 18+
- MongoDB (local or remote instance)

### Backend Setup

1. Configure environment:
```bash
cd backend
cp .env.example .env
# Edit .env with your API keys and MongoDB URL
```

2. Add your API keys to `backend/.env`:
```env
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
MONGODB_URL=mongodb://localhost:27017
```

### Start Everything

Simply run:
```bash
chmod +x start.sh
./start.sh
```

This will:
- Install all Python dependencies with uv
- Install all npm dependencies
- Start the FastAPI backend (port 6969)
- Start the Next.js frontend (port 3000)

### Access the Application

- 🎨 **Frontend**: http://localhost:3000
- 📟 **Backend API**: http://localhost:6969
- 📚 **API Docs**: http://localhost:6969/docs

## Project Structure

```
ai_talking/
├── frontend/              # Next.js frontend
│   ├── app/              # App Router pages
│   │   ├── (chat)/       # Chat route group
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   └── conversation/[id]/page.tsx
│   │   ├── layout.tsx    # Root layout
│   │   └── globals.css
│   ├── components/       # React components
│   │   ├── chat/         # Chat components
│   │   ├── sidebar/      # Sidebar components
│   │   └── ui/           # shadcn/ui components
│   ├── lib/              # Utilities
│   │   ├── api.ts        # API client
│   │   └── websocket.ts  # WebSocket client
│   ├── stores/           # Zustand stores
│   └── package.json
├── backend/              # FastAPI backend
│   ├── src/
│   │   ├── agents/       # Agent system
│   │   ├── api/          # API routes
│   │   ├── core/         # LLM client, streaming
│   │   ├── db/           # MongoDB connection
│   │   └── services/     # Business logic
│   └── pyproject.toml
├── start.sh              # Start script
└── README.md
```

## Available Agents

- **Supervisor**: Intent recognition and routing
- **FinancialAnalysis**: Market analysis, financial data
- **DocumentAnalysis**: PDF/Excel processing and analysis

## Development

### Adding New Agents

1. Create a new agent in `backend/src/agents/`:
```python
from src.agents.base import BaseAgent

class MyCustomAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.name = "MyCustom"
        self.description = "My custom agent"
        self.category = "custom"

    async def execute(self, input_text: str, context: dict = None) -> str:
        # Your implementation
        return "Response"
```

2. Register it in `backend/src/agents/__init__.py`:
```python
agent_registry.register(MyCustomAgent())
```

## License

MIT
