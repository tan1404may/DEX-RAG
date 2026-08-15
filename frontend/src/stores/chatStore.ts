import { create } from 'zustand'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: any[]
  isLoading?: boolean
}

interface ChatStore {
  messages: Message[]
  addMessage: (msg: Message) => void
  updateLastMessage: (content: string, sources?: any[]) => void
  setLoading: (loading: boolean) => void
}

export const useChatStore = create<ChatStore>((set) => ({
  messages: [],
  addMessage: (msg) => set((state) => ({ messages: [...state.messages, msg] })),
  updateLastMessage: (content, sources) =>
    set((state) => {
      const msgs = [...state.messages]
      const last = msgs[msgs.length - 1]
      if (last && last.role === 'assistant') {
        last.content = content
        last.sources = sources
        last.isLoading = false
      }
      return { messages: msgs }
    }),
  setLoading: (loading) =>
    set((state) => {
      const msgs = [...state.messages]
      const last = msgs[msgs.length - 1]
      if (last && last.role === 'assistant') last.isLoading = loading
      return { messages: msgs }
    }),
}))