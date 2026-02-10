"use client"

import { useState, useRef, useEffect } from 'react'
import { Send, Paperclip, X } from 'lucide-react'
import { cn } from '@/lib/utils'
import { api } from '@/lib/api'
import { useI18n } from '@/lib/i18n'

interface ChatInputProps {
  onSendMessage: (content: string, attachments: string[]) => void
  disabled?: boolean
}

export default function ChatInput({ onSendMessage, disabled }: ChatInputProps) {
  const { t } = useI18n()
  const [message, setMessage] = useState('')
  const [attachments, setAttachments] = useState<File[]>([])
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      if (message.trim()) {
        textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`
      } else {
        textareaRef.current.style.height = 'auto'
      }
    }
  }, [message])

  const handleSend = () => {
    if (message.trim() || attachments.length > 0) {
      onSendMessage(message.trim(), attachments.map((f) => f.name))
      setMessage('')
      setAttachments([])
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    setAttachments((prev) => [...prev, ...files])
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const removeAttachment = (index: number) => {
    setAttachments((prev) => prev.filter((_, i) => i !== index))
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const files = Array.from(e.dataTransfer.files).filter(
      (file) => file.type === 'application/pdf' || file.type.startsWith('image/')
    )
    setAttachments((prev) => [...prev, ...files])
  }

  return (
    <div className="border-t border-border p-4 bg-background">
      {/* Attachments Preview */}
      {attachments.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-3">
          {attachments.map((file, index) => (
            <div
              key={index}
              className="flex items-center gap-2 px-3 py-2 bg-secondary rounded-lg text-sm"
            >
              <Paperclip className="w-4 h-4" />
              <span className="max-w-[200px] truncate">{file.name}</span>
              <button
                onClick={() => removeAttachment(index)}
                className="p-1 hover:bg-accent rounded"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Input Area */}
      <div
        className={cn(
          "flex items-end gap-3 p-3 rounded-lg border-2 transition-colors",
          isDragging ? 'border-primary bg-primary/5' : 'border-input'
        )}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {/* File Upload Button */}
        <button
          onClick={() => fileInputRef.current?.click()}
          className="p-2 hover:bg-accent rounded-lg transition-colors"
          title={t('chat.attachments')}
          disabled={disabled}
        >
          <Paperclip className="w-5 h-5 text-muted-foreground" />
        </button>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,image/*"
          className="hidden"
          onChange={handleFileSelect}
          disabled={disabled}
        />

        {/* Text Input */}
        <textarea
          ref={textareaRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={t('chat.sendPlaceholder')}
          className="flex-1 min-h-[44px] max-h-[200px] px-2 py-2 bg-transparent resize-none focus:outline-none text-sm leading-relaxed"
          disabled={disabled}
          rows={1}
        />

        {/* Send Button */}
        <button
          onClick={handleSend}
          disabled={disabled || (!message.trim() && attachments.length === 0)}
          className={cn(
            "p-2 rounded-lg transition-colors",
            (!message.trim() && attachments.length === 0) || disabled
              ? 'bg-muted text-muted-foreground cursor-not-allowed'
              : 'bg-primary text-primary-foreground hover:opacity-90'
          )}
          title={t('chat.sendButton')}
        >
          <Send className="w-5 h-5" />
        </button>
      </div>

      {/* Drag & Drop Hint */}
      {isDragging && (
        <div className="absolute inset-0 flex items-center justify-center bg-background/80 backdrop-blur-sm rounded-lg -z-10">
          <p className="text-sm text-muted-foreground">Drop files here to attach</p>
        </div>
      )}

      {/* Character Counter */}
      {message.length > 0 && (
        <div className="mt-2 text-right">
          <span className="text-xs text-muted-foreground">
            {message.length} characters
          </span>
        </div>
      )}
    </div>
  )
}
