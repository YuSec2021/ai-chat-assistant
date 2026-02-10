"use client"

import { useEffect, useRef, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useConversationStore } from '@/stores/use-conversation-store'
import { api } from '@/lib/api'
import { WebSocketClient } from '@/lib/websocket'
import type { StreamChunk } from '@/lib/websocket'
import ChatMessages from '@/components/chat-messages'
import ChatInput from '@/components/chat-input'

export default function ConversationPage() {
  const params = useParams()
  const router = useRouter()
  const { conversations, tempConversation, setCurrentConversation, addMessage, addConversation, setTempConversation } = useConversationStore()
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const wsRef = useRef<WebSocketClient | null>(null)
  const pendingMessageRef = useRef<{ messageId: string; content: string } | null>(null)

  const convId = params.id as string
  const isTempConv = convId === 'temp-new'
  const conversation = isTempConv ? tempConversation : conversations.find(c => c.id === convId)

  // Set current conversation when it changes
  useEffect(() => {
    if (conversation) {
      setCurrentConversation(conversation)
    }
  }, [conversation, setCurrentConversation])

  // Setup WebSocket connection when convId changes
  useEffect(() => {
    // Don't setup WebSocket for temporary conversations
    if (isTempConv) return

    // Cleanup on unmount or convId change
    return () => {
      if (wsRef.current) {
        wsRef.current.disconnect()
        wsRef.current = null
      }
    }
  }, [convId, isTempConv])

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
        // Use convId which might have been updated if it was a temp conversation
        const actualConvId = wsRef.current?.getConversationId() || convId
        addMessage(actualConvId, assistantMessage)
      }
      pendingMessageRef.current = null
    }
  }, [isStreaming, addMessage])

  const handleSendMessage = async (content: string, attachments: string[] = []) => {
    if (!conversation || isStreaming || isSaving) return

    let actualConvId = convId

    // If this is a temporary conversation, save it to DB first
    if (isTempConv && tempConversation) {
      setIsSaving(true)
      try {
        const newConv = await api.createConversation()

        // The API returns messages, so we need to add the current messages to the DB
        // For now, let's reload conversations to get the latest state
        const allConv = await api.listConversations()
        addConversation(newConv)

        // Update the actual conversation ID
        actualConvId = newConv.id

        // Navigate to the real conversation URL
        router.replace(`/chat/${newConv.id}`)
      } catch (error) {
        console.error('Failed to save conversation:', error)
        return
      } finally {
        setIsSaving(false)
      }
    }

    // 添加用户消息
    const userMessage = {
      id: Date.now().toString(),
      role: 'user' as const,
      content,
      attachments,
      timestamp: new Date().toISOString(),
    }
    addMessage(actualConvId, userMessage)

    // 连接或复用 WebSocket
    if (!wsRef.current) {
      wsRef.current = new WebSocketClient(actualConvId)
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
      <ChatMessages
        messages={conversation.messages}
        streamingContent={isStreaming ? streamingContent : null}
      />
      <ChatInput onSendMessage={handleSendMessage} disabled={isStreaming || isSaving} />
    </>
  )
}
