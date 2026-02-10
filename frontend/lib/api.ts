const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:6969/api'

// Helper to get auth headers
function getAuthHeaders() {
  if (typeof window === 'undefined') return {}

  const token = localStorage.getItem('auth-storage')
  if (!token) return {}

  try {
    const parsed = JSON.parse(token)
    const accessToken = parsed?.state?.token
    return accessToken ? { Authorization: `Bearer ${accessToken}` } : {}
  } catch {
    return {}
  }
}

export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  attachments?: string[]
  timestamp: string
}

export interface Conversation {
  id: string
  title: string
  messages: Message[]
  created_at: string
  updated_at: string
}

export interface CreateConversationResponse {
  conversation_id: string
  title: string
  message_id?: string
  agent?: string
  content?: string
  done?: boolean
  timestamp?: string
}

export const api = {
  async listConversations(): Promise<Conversation[]> {
    const response = await fetch(`${API_BASE_URL}/conversations`, {
      headers: getAuthHeaders()
    })
    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error')
      throw new Error(`Failed to fetch conversations (${response.status}): ${errorText}`)
    }
    return response.json()
  },

  async getConversation(id: string): Promise<Conversation> {
    const response = await fetch(`${API_BASE_URL}/conversations/${id}`, {
      headers: getAuthHeaders()
    })
    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error')
      throw new Error(`Failed to fetch conversation (${response.status}): ${errorText}`)
    }
    return response.json()
  },

  async createConversation(): Promise<Conversation> {
    const response = await fetch(`${API_BASE_URL}/conversations`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify({}),
    })
    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error')
      throw new Error(`Failed to create conversation (${response.status}): ${errorText}`)
    }
    const data: CreateConversationResponse = await response.json()
    return {
      id: data.conversation_id,
      title: data.title,
      messages: [],
      created_at: data.timestamp || new Date().toISOString(),
      updated_at: data.timestamp || new Date().toISOString(),
    }
  },

  async deleteConversation(id: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/conversations/${id}`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    })
    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error')
      throw new Error(`Failed to delete conversation (${response.status}): ${errorText}`)
    }
  },

  async updateConversation(id: string, title: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/conversations/${id}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify({ title }),
    })
    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error')
      throw new Error(`Failed to update conversation (${response.status}): ${errorText}`)
    }
  },

  async uploadFile(file: File): Promise<string> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: formData,
    })

    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error')
      throw new Error(`Failed to upload file (${response.status}): ${errorText}`)
    }

    const data = await response.json()
    return data.file_path
  },
}
