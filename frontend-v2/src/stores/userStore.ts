import { create } from 'zustand'

interface User {
  userId: string
  userName: string
  token: string
}

interface UserState {
  user: User | null
  setUser: (user: User) => void
  clearUser: () => void
}

// 从 localStorage 恢复
const saved = localStorage.getItem('user')
const initialUser: User | null = saved ? (() => { try { return JSON.parse(saved) } catch { return null } })() : null

export const useUserStore = create<UserState>((set) => ({
  user: initialUser,
  setUser: (user) => {
    localStorage.setItem('user', JSON.stringify(user))
    set({ user })
  },
  clearUser: () => {
    localStorage.removeItem('user')
    set({ user: null })
  },
}))
