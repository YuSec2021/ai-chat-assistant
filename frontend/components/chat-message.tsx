"use client"

import { memo } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeRaw from 'rehype-raw'
import rehypeHighlight from 'rehype-highlight'
import { cn } from '@/lib/utils'
import type { Message } from '@/lib/api'
import 'highlight.js/styles/github-dark.css'

interface ChatMessageProps {
  message: Message
  isStreaming?: boolean
}

function ChatMessageComponent({ message, isStreaming }: ChatMessageProps) {
  const isUser = message.role === 'user'

  return (
    <div
      className={cn(
        "flex gap-4 group",
        isUser ? 'justify-end' : 'justify-start'
      )}
    >
      {/* Avatar */}
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center flex-shrink-0">
          <span className="text-sm font-semibold text-white">AI</span>
        </div>
      )}

      {/* Message Content */}
      <div
        className={cn(
          "max-w-[80%] rounded-2xl px-4 py-3",
          isUser
            ? 'bg-primary text-primary-foreground'
            : 'bg-muted'
        )}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap break-words text-sm leading-relaxed">
            {message.content}
          </p>
        ) : (
          <div className="prose prose-sm dark:prose-invert max-w-none">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[rehypeRaw, rehypeHighlight]}
              components={{
                // Custom code block styling
                pre: ({ node, ...props }) => (
                  <div className="relative group">
                    <pre {...props} className="bg-muted p-4 rounded-lg overflow-x-auto" />
                  </div>
                ),
              }}
            >
              {message.content}
            </ReactMarkdown>
            {isStreaming && <span className="inline-block w-2 h-4 bg-primary animate-pulse ml-1" />}
          </div>
        )}
      </div>

      {/* User Avatar */}
      {isUser && (
        <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center flex-shrink-0">
          <span className="text-sm font-semibold">U</span>
        </div>
      )}
    </div>
  )
}

export default memo(ChatMessageComponent)
