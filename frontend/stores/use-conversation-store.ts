import { create } from 'zustand'
import type { Message, Conversation } from '@/lib/api'

interface ConversationStore {
  conversations: Conversation[]
  currentConversation: Conversation | null
  tempConversation: Conversation | null  // Temporary conversation not yet saved
  setConversations: (conversations: Conversation[]) => void
  setCurrentConversation: (conversation: Conversation | null) => void
  addConversation: (conversation: Conversation) => void
  removeConversation: (id: string) => void
  updateConversation: (id: string, title: string) => void
  addMessage: (conversationId: string, message: Message) => void
  setTempConversation: (conversation: Conversation) => void  // Set temporary conversation
  clearTempConversation: () => void  // Clear temporary conversation
}

export const useConversationStore = create<ConversationStore>((set) => ({
  conversations: [],
  currentConversation: null,
  tempConversation: null,

  setConversations: (conversations) => set({ conversations }),

  setCurrentConversation: (conversation) => set({ currentConversation: conversation }),

  setTempConversation: (conversation) => set({ tempConversation: conversation, currentConversation: conversation }),

  clearTempConversation: () => set({ tempConversation: null }),

  addConversation: (conversation) =>
    set((state) => ({
      conversations: [conversation, ...state.conversations],
      currentConversation: state.tempConversation?.id === 'temp-new' ? conversation : state.currentConversation,
      tempConversation: state.tempConversation?.id === 'temp-new' ? null : state.tempConversation,
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
    set((state) => {
      const updateConv = (conv: Conversation) => ({
        ...conv,
        messages: [...conv.messages, message],
        updated_at: new Date().toISOString(),
      })

      return {
        conversations: state.conversations.map((conv) =>
          conv.id === conversationId ? updateConv(conv) : conv
        ),
        currentConversation:
          state.currentConversation?.id === conversationId
            ? updateConv(state.currentConversation)
            : state.currentConversation,
        tempConversation:
          state.tempConversation?.id === conversationId
            ? updateConv(state.tempConversation)
            : state.tempConversation,
      }
    }),
}))
