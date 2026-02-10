"use client"

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useConversationStore } from '@/stores/use-conversation-store'
import { useAuthStore } from '@/stores/useAuthStore'
import { api } from '@/lib/api'
import ChatSidebar from '@/components/chat-sidebar'
import ChatMain from '@/components/chat-main'
import ChatHeader from '@/components/chat-header'

export default function ChatLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const router = useRouter()
  const { isAuthenticated, token, hasHydrated } = useAuthStore()
  const { setConversations, currentConversation } = useConversationStore()
  const [hasMounted, setHasMounted] = useState(false)

  // Wait for client-side mount
  useEffect(() => {
    setHasMounted(true)
  }, [])

  useEffect(() => {
    // Only check auth after hydration is complete
    if (!hasHydrated || !hasMounted) {
      return
    }

    // Check if user is authenticated
    if (!isAuthenticated || !token) {
      router.push('/login')
      return
    }

    loadConversations()
  }, [isAuthenticated, token, hasHydrated, hasMounted])

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

  // Show loading while hydrating
  if (!hasHydrated || !hasMounted) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary mb-4"></div>
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    )
  }

  // Don't render if not authenticated
  if (!isAuthenticated || !token) {
    return null
  }

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      <ChatSidebar />
      <ChatMain>
        {/* Global Header - always visible */}
        <ChatHeader conversation={currentConversation} />
        {/* Page content */}
        {children}
      </ChatMain>
    </div>
  )
}
