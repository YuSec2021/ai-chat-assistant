"use client"

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useConversationStore } from '@/stores/use-conversation-store'
import { useAuthStore } from '@/stores/useAuthStore'
import { api } from '@/lib/api'
import ChatSidebar from '@/components/chat-sidebar'
import ChatMain from '@/components/chat-main'

export default function ChatLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const router = useRouter()
  const { isAuthenticated, token } = useAuthStore()
  const { setConversations } = useConversationStore()

  useEffect(() => {
    // Check if user is authenticated
    if (!isAuthenticated || !token) {
      router.push('/login')
      return
    }

    loadConversations()
  }, [isAuthenticated, token])

  const loadConversations = async () => {
    try {
      const conversations = await api.listConversations()
      setConversations(conversations)
    } catch (error) {
      console.error('Failed to load conversations:', error)
      // If unauthorized, redirect to login
      if (error instanceof Error && error.message.includes('401')) {
        router.push('/login')
      }
    }
  }

  // Don't render if not authenticated
  if (!isAuthenticated || !token) {
    return null
  }

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      <ChatSidebar />
      <ChatMain>{children}</ChatMain>
    </div>
  )
}
