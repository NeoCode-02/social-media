import { create } from 'zustand'

interface RealtimeState {
  online: Record<string, boolean>
  // chatId -> set of user ids currently typing
  typing: Record<string, string[]>
  setPresence: (userId: string, online: boolean) => void
  setTyping: (chatId: string, userId: string, isTyping: boolean) => void
}

export const useRealtimeStore = create<RealtimeState>((set) => ({
  online: {},
  typing: {},
  setPresence: (userId, online) =>
    set((s) => ({ online: { ...s.online, [userId]: online } })),
  setTyping: (chatId, userId, isTyping) =>
    set((s) => {
      const current = s.typing[chatId] ?? []
      const next = isTyping
        ? current.includes(userId)
          ? current
          : [...current, userId]
        : current.filter((id) => id !== userId)
      return { typing: { ...s.typing, [chatId]: next } }
    }),
}))
