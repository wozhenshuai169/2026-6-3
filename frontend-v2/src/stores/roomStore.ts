import { create } from 'zustand'
import type { Member, RoomMessage } from '../api/types'

interface RoomState {
  roomId: string | null
  roomName: string
  leaderId: string | null      // 团长 userId（从第一个创建者推断）
  members: Member[]
  currentSpot: string
  status: string
  messages: RoomMessage[]

  setRoom: (data: { roomId: string; roomName?: string; leaderId?: string; members: Member[]; currentSpot: string; status: string }) => void
  setMembers: (members: Member[]) => void
  setCurrentSpot: (spot: string) => void
  addMessage: (msg: RoomMessage) => void
  clearMessages: () => void
  reset: () => void
}

export const useRoomStore = create<RoomState>((set) => ({
  roomId: null,
  roomName: '',
  leaderId: null,
  members: [],
  currentSpot: '',
  status: '',
  messages: [],

  setRoom: (data) => set({
    roomId: data.roomId,
    roomName: data.roomName || '',
    leaderId: data.leaderId || null,
    members: data.members,
    currentSpot: data.currentSpot,
    status: data.status,
  }),
  setMembers: (members) => set({ members }),
  setCurrentSpot: (currentSpot) => set({ currentSpot }),
  addMessage: (msg) => set((s) => ({ messages: [...s.messages.slice(-99), msg] })),
  clearMessages: () => set({ messages: [] }),
  reset: () => set({ roomId: null, roomName: '', leaderId: null, members: [], currentSpot: '', status: '', messages: [] }),
}))
