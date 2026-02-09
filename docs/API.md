# AI Chat Assistant - Backend API Documentation

**Version:** 1.0.0
**Base URL:** `http://localhost:6969`
**API Prefix:** `/api`
**Interactive Docs:** [http://localhost:6969/docs](http://localhost:6969/docs)

---

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Data Models](#data-models)
- [API Endpoints](#api-endpoints)
  - [Conversations](#conversations)
  - [Chat](#chat)
  - [File Upload](#file-upload)
  - [System](#system)
- [WebSocket](#websocket)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)

---

## Overview

The AI Chat Assistant API provides endpoints for managing conversations, sending messages with AI responses, file uploads, and real-time streaming via WebSocket.

**Key Features:**
- RESTful API design
- WebSocket support for streaming responses
- Agent routing system (Supervisor, FinancialAnalysis, DocumentAnalysis)
- File attachment support (images, PDFs, Excel)
- MongoDB-backed conversation storage
- OpenAI/Anthropic LLM integration

---

## Authentication

> **Note:** Current version does not require authentication.
> Future versions will implement API key or JWT-based authentication.

---

## Data Models

### Conversation

```typescript
{
  id: string                    // Unique conversation ID
  title: string                 // Conversation title
  messages: Message[]           // Array of messages
  created_at: datetime          // Creation timestamp
  updated_at: datetime          // Last update timestamp
  metadata: object              // Additional metadata
}
```

### Message

```typescript
{
  id: string                    // Unique message ID
  role: "user" | "assistant" | "system"
  content: string               // Message content (text/markdown)
  attachments: string[]         // Array of file IDs
  metadata: object              // Additional metadata
  timestamp: datetime           // Message timestamp
}
```

### ChatResponse

```typescript
{
  message_id: string            // Response message ID
  content: string               // AI response content
  done: boolean                 // Stream completion status
  metadata: object              // Additional metadata
}
```

### FileUpload

```typescript
{
  file_id: string               // Unique file ID
  filename: string              // Original filename
  mime_type: string             // File MIME type
  size: number                  // File size in bytes
  temp_path: string             // Temporary file path
}
```

### AgentInfo

```typescript
{
  name: string                  // Agent name
  description: string           // Agent description
  category: string              // Agent category
}
```

---

## API Endpoints

### Conversations

#### List All Conversations

```http
GET /api/conversations
```

**Response:** `200 OK`

```json
{
  "conversations": [
    {
      "id": "uuid-string",
      "title": "Financial Analysis",
      "messages": [],
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "metadata": {}
    }
  ]
}
```

---

#### Create Conversation

```http
POST /api/conversations
```

**Request Body:**

```json
{
  "title": "New Conversation"  // Optional, defaults to "New Conversation"
}
```

**Response:** `201 Created`

```json
{
  "id": "uuid-string",
  "title": "New Conversation",
  "messages": [],
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "metadata": {}
}
```

---

#### Get Conversation

```http
GET /api/conversations/{conv_id}
```

**Path Parameters:**
- `conv_id` (string) - Conversation ID (UUID or ObjectId)

**Response:** `200 OK`

```json
{
  "id": "uuid-string",
  "title": "Financial Analysis",
  "messages": [
    {
      "id": "msg-id",
      "role": "user",
      "content": "Analyze AAPL stock",
      "attachments": [],
      "timestamp": "2024-01-01T00:00:00Z"
    },
    {
      "id": "msg-id-2",
      "role": "assistant",
      "content": "Based on the analysis...",
      "timestamp": "2024-01-01T00:00:01Z"
    }
  ],
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:01Z",
  "metadata": {}
}
```

**Error Responses:**
- `404 Not Found` - Conversation not found

---

#### Update Conversation

```http
PATCH /api/conversations/{conv_id}
```

**Path Parameters:**
- `conv_id` (string) - Conversation ID

**Request Body:**

```json
{
  "title": "Updated Title"  // Optional
}
```

**Response:** `200 OK`

Returns updated conversation object.

**Error Responses:**
- `404 Not Found` - Conversation not found

---

#### Delete Conversation

```http
DELETE /api/conversations/{conv_id}
```

**Path Parameters:**
- `conv_id` (string) - Conversation ID

**Response:** `200 OK`

```json
{
  "message": "Conversation deleted"
}
```

**Error Responses:**
- `404 Not Found` - Conversation not found

---

#### Get Conversation Messages

```http
GET /api/conversations/{conv_id}/messages
```

**Path Parameters:**
- `conv_id` (string) - Conversation ID

**Response:** `200 OK`

```json
{
  "messages": [
    {
      "id": "msg-id",
      "role": "user",
      "content": "Hello",
      "attachments": [],
      "timestamp": "2024-01-01T00:00:00Z"
    }
  ]
}
```

**Error Responses:**
- `404 Not Found` - Conversation not found

---

### Chat

#### Send Message (Non-Streaming)

```http
POST /api/chat/{conv_id}
```

**Path Parameters:**
- `conv_id` (string) - Conversation ID

**Request Body:**

```json
{
  "content": "Your message here",
  "attachments": ["file-id-1", "file-id-2"]  // Optional
}
```

**Response:** `200 OK`

```json
{
  "message_id": "uuid-string",
  "content": "AI response here...",
  "done": true,
  "metadata": {}
}
```

**Error Responses:**
- `404 Not Found` - Conversation not found
- `500 Internal Server Error` - LLM processing error

---

### File Upload

#### Upload File

```http
POST /api/upload
```

**Content-Type:** `multipart/form-data`

**Form Data:**
- `file` (file) - File to upload

**Supported File Types:**
- Images: `image/png`, `image/jpeg`, `image/gif`, `image/webp`
- Video: `video/mp4`, `video/webp`
- Documents: `application/pdf`

**Maximum File Size:** 10MB

**Response:** `200 OK`

```json
{
  "file_id": "uuid-string",
  "filename": "document.pdf",
  "mime_type": "application/pdf",
  "size": 1024000,
  "temp_path": "/tmp/uploads/uuid-string.pdf"
}
```

**Error Responses:**
- `413 Payload Too Large` - File exceeds size limit
- `415 Unsupported Media Type` - Invalid file type
- `500 Internal Server Error` - Upload failed

---

#### Get Uploaded File

```http
GET /api/upload/files/{file_id}
```

**Path Parameters:**
- `file_id` (string) - File ID

**Response:** `200 OK`

Returns the file content.

**Error Responses:**
- `404 Not Found` - File not found or expired

---

### System

#### Health Check

```http
GET /health
```

**Response:** `200 OK`

```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

---

#### Root Endpoint

```http
GET /
```

**Response:** `200 OK`

```json
{
  "message": "AI Chat Assistant API",
  "version": "1.0.0",
  "docs": "/docs",
  "health": "/health"
}
```

---

#### List Available Agents

```http
GET /api/agents
```

**Response:** `200 OK`

```json
{
  "agents": [
    {
      "name": "Supervisor",
      "description": "Routes requests to appropriate specialized agents",
      "category": "routing"
    },
    {
      "name": "FinancialAnalysis",
      "description": "Analyzes financial data and market trends",
      "category": "finance"
    },
    {
      "name": "DocumentAnalysis",
      "description": "Processes and analyzes documents (PDF, Excel)",
      "category": "document"
    }
  ]
}
```

---

## WebSocket

### Streaming Chat Endpoint

```javascript
const ws = new WebSocket('ws://localhost:6969/api/chat/ws/{conv_id}');

// Send message
ws.send(JSON.stringify({
  content: "Your message here",
  attachments: ["file-id"]  // Optional
}));

// Receive streaming chunks
ws.onmessage = (event) => {
  const chunk = JSON.parse(event.data);

  if (chunk.error) {
    console.error('Error:', chunk.error);
    return;
  }

  if (!chunk.done) {
    // Streaming content
    console.log(chunk.content);
    // Append to UI
  } else {
    // Stream complete
    console.log('Complete! Message ID:', chunk.metadata.message_id);
  }
};
```

#### WebSocket Message Format

**Request (Client → Server):**

```json
{
  "content": "Your message",
  "attachments": ["file-id-1"]  // Optional
}
```

**Response (Server → Client):**

```json
{
  "content": "Partial response...",
  "done": false,
  "metadata": {
    "message_id": "uuid-string"
  }
}
```

**Final Chunk:**

```json
{
  "content": "",
  "done": true,
  "metadata": {
    "message_id": "uuid-string"
  }
}
```

**Error Response:**

```json
{
  "content": "",
  "done": true,
  "metadata": {
    "message_id": "uuid-string"
  },
  "error": "Error message here"
}
```

---

## Error Handling

All endpoints may return the following error responses:

### 400 Bad Request

```json
{
  "detail": "Invalid request data"
}
```

### 404 Not Found

```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error

```json
{
  "detail": "Internal server error message"
}
```

### 422 Validation Error

```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "Field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Rate Limiting

> **Note:** Rate limiting is not currently implemented.
> Future versions will include rate limiting based on API keys or IP addresses.

---

## Examples

### Example 1: Complete Chat Flow

```bash
# 1. Create a conversation
curl -X POST http://localhost:6969/api/conversations \
  -H "Content-Type: application/json" \
  -d '{"title": "Financial Analysis"}'

# Response: {"id": "conv-uuid", ...}

# 2. Send a message
curl -X POST http://localhost:6969/api/chat/conv-uuid \
  -H "Content-Type: application/json" \
  -d '{"content": "Analyze AAPL stock trends"}'

# 3. Get conversation history
curl http://localhost:6969/api/conversations/conv-uuid
```

### Example 2: Upload File and Chat

```bash
# 1. Upload a file
curl -X POST http://localhost:6969/api/upload \
  -F "file=@document.pdf"

# Response: {"file_id": "file-uuid", ...}

# 2. Send message with attachment
curl -X POST http://localhost:6969/api/chat/conv-uuid \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Summarize this document",
    "attachments": ["file-uuid"]
  }'
```

### Example 3: WebSocket Streaming (JavaScript)

```javascript
const convId = 'conv-uuid';
const ws = new WebSocket(`ws://localhost:6969/api/chat/ws/${convId});

ws.onopen = () => {
  console.log('Connected to WebSocket');

  // Send message
  ws.send(JSON.stringify({
    content: 'Tell me about AI trends'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.error) {
    console.error('Error:', data.error);
    return;
  }

  if (!data.done) {
    // Append streaming content to UI
    appendToChat(data.content);
  } else {
    console.log('Stream complete!');
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('WebSocket closed');
};
```

---

## SDK Examples

### Python (using httpx)

```python
import httpx

class ChatAssistant:
    def __init__(self, base_url="http://localhost:6969"):
        self.client = httpx.Client(base_url=base_url)

    def create_conversation(self, title="New Chat"):
        response = self.client.post(
            "/api/conversations",
            json={"title": title}
        )
        return response.json()

    def send_message(self, conv_id, content, attachments=None):
        response = self.client.post(
            f"/api/chat/{conv_id}",
            json={
                "content": content,
                "attachments": attachments or []
            }
        )
        return response.json()

    def upload_file(self, file_path):
        with open(file_path, "rb") as f:
            files = {"file": f}
            response = self.client.post("/api/upload", files=files)
        return response.json()

# Usage
assistant = ChatAssistant()
conv = assistant.create_conversation("My Chat")
response = assistant.send_message(conv["id"], "Hello!")
print(response["content"])
```

### JavaScript/TypeScript

```typescript
class ChatAssistant {
  private baseUrl: string;

  constructor(baseUrl: string = 'http://localhost:6969') {
    this.baseUrl = baseUrl;
  }

  async createConversation(title: string = 'New Chat') {
    const response = await fetch(`${this.baseUrl}/api/conversations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title })
    });
    return response.json();
  }

  async sendMessage(convId: string, content: string, attachments: string[] = []) {
    const response = await fetch(`${this.baseUrl}/api/chat/${convId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content, attachments })
    });
    return response.json();
  }

  async uploadFile(file: File) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/api/upload`, {
      method: 'POST',
      body: formData
    });
    return response.json();
  }
}

// Usage
const assistant = new ChatAssistant();
const conv = await assistant.createConversation('My Chat');
const response = await assistant.sendMessage(conv.id, 'Hello!');
console.log(response.content);
```

---

## Interactive API Documentation

The backend includes automatic interactive API documentation powered by FastAPI:

- **Swagger UI:** [http://localhost:6969/docs](http://localhost:6969/docs)
- **ReDoc:** [http://localhost:6969/redoc](http://localhost:6969/redoc)

These provide:
- Interactive API explorer
- Request/response examples
- Schema validation
- Try-it-out functionality

---

## Configuration

The API behavior can be configured via environment variables in `backend/.env`:

```env
# Server
HOST=0.0.0.0
PORT=6969
DEBUG=false

# Database
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=ai_chat_assistant

# LLM API
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
DEFAULT_LLM_PROVIDER=openai
DEFAULT_MODEL=gpt-4

# File Upload
MAX_UPLOAD_SIZE=10485760  # 10MB in bytes
ALLOWED_FILE_TYPES=image/png,image/jpeg,image/gif,image/webp,video/mp4,video/webp,application/pdf

# Temp File Cleanup
TEMP_FILE_CLEANUP_INTERVAL=24  # hours
```

---

## Support

For issues or questions:
- Check the [main README](../README.md)
- Open an issue on GitHub
- Review the interactive API docs at `/docs`
