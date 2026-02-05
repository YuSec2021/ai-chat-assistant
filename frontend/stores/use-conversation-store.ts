import { create } from 'zustand'
import type { Message, Conversation } from '@/lib/api'

interface ConversationStore {
  conversations: Conversation[]
  currentConversation: Conversation | null
  setConversations: (conversations: Conversation[]) => void
  setCurrentConversation: (conversation: Conversation | null) => void
  addConversation: (conversation: Conversation) => void
  removeConversation: (id: string) => void
  updateConversation: (id: string, title: string) => void
  addMessage: (conversationId: string, message: Message) => void
}

export const useConversationStore = create<ConversationStore>((set) => ({
  conversations: [],
  currentConversation: null,

  setConversations: (conversations) => set({ conversations }),

  setCurrentConversation: (conversation) => set({ currentConversation: conversation }),

  addConversation: (conversation) =>
    set((state) => ({
      conversations: [conversation, ...state.conversations],
    })),

  removeConversation: (id) =>
    set((state) => ({
      conversations: state.conversations.filter((c) => c.id !== id),
      currentConversation:
        state.currentConversation?.id === id ? null : state.currentConversation,
    })),

  updateConversation: (id, title) =>
    set((state) => ({
      conversations: state.conversations.map((c) =>
        c.id === id ? { ...c, title } : c
      ),
      currentConversation:
        state.currentConversation?.id === id
          ? { ...state.currentConversation, title }
          : state.currentConversation,
    })),

  addMessage: (conversationId, message) =>
    set((state) => ({
      conversations: state.conversations.map((conv) =>
        conv.id === conversationId
          ? {
              ...conv,
              messages: [...conv.messages, message],
              updated_at: new Date().toISOString(),
            }
          : conv
      ),
      currentConversation:
        state.currentConversation?.id === conversationId
          ? {
              ...state.currentConversation,
              messages: [...state.currentConversation.messages, message],
              updated_at: new Date().toISOString(),
            }
          : state.currentConversation,
    })),
}))
