"use client"

import { useEffect, useRef, useState } from 'react'
import { useParams } from 'next/navigation'
import { useConversationStore } from '@/stores/use-conversation-store'
import { WebSocketClient } from '@/lib/websocket'
import type { StreamChunk } from '@/lib/websocket'
import ChatMessages from '@/components/chat-messages'
import ChatInput from '@/components/chat-input'
import ChatHeader from '@/components/chat-header'

export default function ConversationPage() {
  const params = useParams()
  const { conversations, setCurrentConversation, addMessage } = useConversationStore()
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')
  const wsRef = useRef<WebSocketClient | null>(null)
  const pendingMessageRef = useRef<{ messageId: string; content: string } | null>(null)

  const convId = params.id as string
  const conversation = conversations.find(c => c.id === convId)

  // Set current conversation when it changes
  useEffect(() => {
    if (conversation) {
      setCurrentConversation(conversation)
    }
  }, [conversation, setCurrentConversation])

  // Setup WebSocket connection when convId changes
  useEffect(() => {
    // Cleanup on unmount or convId change
    return () => {
      if (wsRef.current) {
        wsRef.current.disconnect()
        wsRef.current = null
      }
    }
  }, [convId])

  // Handle pending message when streaming completes
  useEffect(() => {
    if (!isStreaming && pendingMessageRef.current && pendingMessageRef.current.content) {
      const { messageId, content } = pendingMessageRef.current
      if (content.trim()) {
        const assistantMessage = {
          id: messageId,
          role: 'assistant' as const,
          content,
          attachments: [],
          timestamp: new Date().toISOString(),
        }
        addMessage(convId, assistantMessage)
      }
      pendingMessageRef.current = null
    }
  }, [isStreaming, convId, addMessage])

  const handleSendMessage = async (content: string, attachments: string[] = []) => {
    if (!conversation || isStreaming) return

    // 添加用户消息
    const userMessage = {
      id: Date.now().toString(),
      role: 'user' as const,
      content,
      attachments,
      timestamp: new Date().toISOString(),
    }
    addMessage(convId, userMessage)

    // 连接或复用 WebSocket
    if (!wsRef.current) {
      wsRef.current = new WebSocketClient(convId)
      wsRef.current.onMessage = (chunk: StreamChunk) => {
        if (chunk.content) {
          setStreamingContent((prev) => prev + chunk.content)
        }
        if (chunk.done) {
          // Store the pending message to be added in useEffect
          const messageId = chunk.metadata?.message_id || Date.now().toString()
          setStreamingContent((currentContent) => {
            pendingMessageRef.current = { messageId, content: currentContent }
            setIsStreaming(false)
            return '' // Clear streaming content
          })
        }
        if (chunk.error) {
          console.error('Stream error:', chunk.error)
          setIsStreaming(false)
          setStreamingContent('')
          pendingMessageRef.current = null
        }
      }
    }

    // 等待连接建立
    if (!wsRef.current.isConnected()) {
      await wsRef.current.connect()
    }

    setIsStreaming(true)
    setStreamingContent('')
    pendingMessageRef.current = null

    // 发送消息
    wsRef.current.send({ content, attachments })
  }

  if (!conversation) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-xl font-semibold mb-2">Conversation not found</h2>
          <p className="text-muted-foreground">The conversation may have been deleted</p>
        </div>
      </div>
    )
  }

  return (
    <>
      <ChatHeader conversation={conversation} />
      <ChatMessages
        messages={conversation.messages}
        streamingContent={isStreaming ? streamingContent : null}
      />
      <ChatInput onSendMessage={handleSendMessage} disabled={isStreaming} />
    </>
  )
}
