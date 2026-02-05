"use client"

import { useEffect, useRef } from 'react'
import { useConversationStore } from '@/stores/use-conversation-store'
import type { Message } from '@/lib/api'
import ChatMessage from './chat-message'

interface ChatMessagesProps {
  messages: Message[]
  streamingContent?: string | null
}

export default function ChatMessages({ messages, streamingContent }: ChatMessagesProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingContent])

  if (messages.length === 0 && !streamingContent) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="text-center text-muted-foreground max-w-md">
          <p className="text-lg mb-2">Start a conversation</p>
          <p className="text-sm">Send a message to begin chatting with the AI assistant</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-4xl mx-auto px-6 py-6 space-y-6">
        {messages.map((message, index) => (
          <ChatMessage key={message.id || index} message={message} />
        ))}
        {streamingContent && (
          <ChatMessage
            message={{
              id: 'streaming',
              role: 'assistant',
              content: streamingContent,
              attachments: [],
              timestamp: new Date().toISOString(),
            }}
            isStreaming
          />
        )}
        <div ref={messagesEndRef} />
      </div>
    </div>
  )
}
