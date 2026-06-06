import { create } from 'zustand'
import type { PrivateMessage } from '../api/types'

interface ChatStore {
  // 私人消息历史，key = userId
  privateChats: Record<string, PrivateMessage[]>
  addPrivateMessage: (msg: PrivateMessage) => void
}

export const useChatStore = create<ChatStore>((set) => ({
  privateChats: {},
  addPrivateMessage: (msg) =>
    set((s) => {
      const partnerId = msg.fromUserId === msg.toUserId ? msg.fromUserId
        : msg.fromUserId === msg.toUserId ? msg.toUserId
        : [msg.fromUserId, msg.toUserId].find((id) => id !== 'me') || msg.fromUserId
      const key = partnerId
      const existing = s.privateChats[key] || []
      return { privateChats: { ...s.privateChats, [key]: [...existing, msg] } }
    }),
}))
