"use client"

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useConversationStore } from '@/stores/use-conversation-store'
import { api } from '@/lib/api'
import WelcomeScreen from '@/components/welcome-screen'

export default function NewChatPage() {
  const { setConversations, setCurrentConversation } = useConversationStore()
  const router = useRouter()

  useEffect(() => {
    createNewConversation()
  }, [])

  const createNewConversation = async () => {
    try {
      const newConv = await api.createConversation()
      const conversations = await api.listConversations()
      setConversations(conversations)
      setCurrentConversation(newConv)
      router.push(`/chat/${newConv.id}`)
    } catch (error) {
      console.error('Failed to create conversation:', error)
      router.push('/chat/default')
    }
  }

  return <WelcomeScreen />
}
