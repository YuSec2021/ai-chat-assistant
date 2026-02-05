"use client"

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useConversationStore } from '@/stores/use-conversation-store'
import { api } from '@/lib/api'
import { Plus, MessageSquare, Search, Trash2, Edit2, Check, X } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ChatSidebarProps {
  className?: string
}

export default function ChatSidebar({ className }: ChatSidebarProps) {
  const { conversations, currentConversation, removeConversation, updateConversation } = useConversationStore()
  const [searchQuery, setSearchQuery] = useState('')
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editTitle, setEditTitle] = useState('')
  const router = useRouter()

  const filteredConversations = conversations.filter((conv) =>
    conv.title.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const handleNewChat = async () => {
    try {
      const newConv = await api.createConversation()
      const all = await api.listConversations()
      useConversationStore.getState().setConversations(all)
      useConversationStore.getState().setCurrentConversation(newConv)
      router.push(`/chat/${newConv.id}`)
    } catch (error) {
      console.error('Failed to create conversation:', error)
    }
  }

  const handleSelect = (conv: any) => {
    useConversationStore.getState().setCurrentConversation(conv)
    router.push(`/chat/${conv.id}`)
  }

  const handleDelete = async (id: string) => {
    try {
      await api.deleteConversation(id)
      removeConversation(id)
      if (currentConversation?.id === id) {
        handleNewChat()
      }
    } catch (error) {
      console.error('Failed to delete conversation:', error)
    }
  }

  const startEdit = (id: string, title: string) => {
    setEditingId(id)
    setEditTitle(title)
  }

  const saveEdit = async (id: string) => {
    try {
      await api.updateConversation(id, editTitle)
      updateConversation(id, editTitle)
      setEditingId(null)
    } catch (error) {
      console.error('Failed to update conversation:', error)
    }
  }

  const cancelEdit = () => {
    setEditingId(null)
    setEditTitle('')
  }

  return (
    <div className={cn("w-72 bg-secondary border-r border-border flex flex-col", className)}>
      {/* Header */}
      <div className="p-3 border-b border-border">
        <button
          onClick={handleNewChat}
          className="w-full flex items-center gap-2 px-3 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity text-sm font-medium"
        >
          <Plus className="w-4 h-4" />
          <span>New chat</span>
        </button>
      </div>

      {/* Search */}
      <div className="p-3">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search conversations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-background border border-input rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
      </div>

      {/* Conversation List */}
      <div className="flex-1 overflow-y-auto px-2 pb-2">
        {filteredConversations.length === 0 ? (
          <div className="text-center py-8 text-sm text-muted-foreground">
            {searchQuery ? 'No conversations found' : 'No conversations yet'}
          </div>
        ) : (
          filteredConversations.map((conv) => (
            <div
              key={conv.id}
              className={cn(
                "group flex items-center gap-2 px-3 py-2 rounded-lg mb-1 cursor-pointer transition-colors",
                currentConversation?.id === conv.id
                  ? 'bg-accent'
                  : 'hover:bg-muted'
              )}
              onClick={() => editingId === null && handleSelect(conv)}
            >
              <MessageSquare className="w-4 h-4 flex-shrink-0 text-muted-foreground" />

              {editingId === conv.id ? (
                <div className="flex-1 flex items-center gap-2">
                  <input
                    type="text"
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                    className="flex-1 px-2 py-1 bg-background border border-input rounded text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                    autoFocus
                    onClick={(e) => e.stopPropagation()}
                  />
                  <button
                    onClick={(e) => { e.stopPropagation(); saveEdit(conv.id) }}
                    className="p-1 hover:bg-accent rounded"
                  >
                    <Check className="w-3 h-3 text-green-600" />
                  </button>
                  <button
                    onClick={(e) => { e.stopPropagation(); cancelEdit() }}
                    className="p-1 hover:bg-accent rounded"
                  >
                    <X className="w-3 h-3 text-red-600" />
                  </button>
                </div>
              ) : (
                <>
                  <span className="flex-1 truncate text-sm">{conv.title}</span>
                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={(e) => { e.stopPropagation(); startEdit(conv.id, conv.title) }}
                      className="p-1 hover:bg-accent rounded"
                    >
                      <Edit2 className="w-3 h-3" />
                    </button>
                    <button
                      onClick={(e) => { e.stopPropagation(); if (confirm('Delete this conversation?')) handleDelete(conv.id) }}
                      className="p-1 hover:bg-accent rounded hover:text-destructive"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                </>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}
