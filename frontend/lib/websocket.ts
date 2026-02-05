const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:6969/api/chat/ws'

export interface StreamChunk {
  content?: string
  done?: boolean
  error?: string
  metadata?: {
    message_id?: string
    agent?: string
    [key: string]: any
  }
}

export type MessageHandler = (chunk: StreamChunk) => void

export class WebSocketClient {
  private ws: WebSocket | null = null
  private conversationId: string
  private reconnectAttempts = 0
  private maxReconnectAttempts = 3
  public onMessage: MessageHandler = () => {}

  constructor(conversationId: string) {
    this.conversationId = conversationId
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(`${WS_URL}/${this.conversationId}`)

        this.ws.onopen = () => {
          console.log('WebSocket connected')
          this.reconnectAttempts = 0
          resolve()
        }

        this.ws.onmessage = (event) => {
          try {
            const chunk: StreamChunk = JSON.parse(event.data)
            this.onMessage(chunk)
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error)
          }
        }

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error)
          reject(error)
        }

        this.ws.onclose = () => {
          console.log('WebSocket closed')
          // Attempt to reconnect if not intentionally closed
          if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++
            setTimeout(() => {
              console.log(`Reconnecting... attempt ${this.reconnectAttempts}`)
              this.connect()
            }, 1000 * this.reconnectAttempts)
          }
        }
      } catch (error) {
        console.error('Failed to create WebSocket connection:', error)
        reject(error)
      }
    })
  }

  send(data: { content: string; attachments?: string[] }) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    } else {
      console.error('WebSocket is not connected')
    }
  }

  disconnect() {
    if (this.ws) {
      this.reconnectAttempts = this.maxReconnectAttempts // Prevent reconnection
      this.ws.close()
      this.ws = null
    }
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN
  }
}
