"use client"

import { useEffect } from 'react'
import { useConversationStore } from '@/stores/use-conversation-store'
import { api } from '@/lib/api'
import ChatSidebar from '@/components/chat-sidebar'
import ChatMain from '@/components/chat-main'

export default function ChatLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { setConversations } = useConversationStore()

  useEffect(() => {
    loadConversations()
  }, [])

  const loadConversations = async () => {
    try {
      const conversations = await api.listConversations()
      setConversations(conversations)
    } catch (error) {
      console.error('Failed to load conversations:', error)
    }
  }

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      <ChatSidebar />
      <ChatMain>{children}</ChatMain>
    </div>
  )
}
