"use client"

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useConversationStore } from '@/stores/use-conversation-store'
import WelcomeScreen from '@/components/welcome-screen'

export default function NewChatPage() {
  const { setTempConversation } = useConversationStore()
  const router = useRouter()

  useEffect(() => {
    // Create a temporary conversation in memory (not saved to DB yet)
    const tempConv = {
      id: 'temp-new',
      title: 'New Chat',
      messages: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
    setTempConversation(tempConv)
    // Navigate to the temp conversation page
    router.push(`/chat/temp-new`)
  }, [router, setTempConversation])

  return <WelcomeScreen />
}
