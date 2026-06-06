import { create } from 'zustand'

type PanelTab = 'chat' | 'members' | 'assistant' | 'routes' | 'camera'

interface UIState {
  panelOpen: boolean
  panelTab: PanelTab
  setPanelTab: (tab: PanelTab) => void
  togglePanel: () => void
  openPanel: (tab?: PanelTab) => void
  closePanel: () => void

  privateChatUserId: string | null
  privateChatUserName: string | null
  openPrivateChat: (userId: string, userName: string) => void
  closePrivateChat: () => void

  loading: boolean
  loadingText: string
  setLoading: (loading: boolean, text?: string) => void
}

export const useUIStore = create<UIState>((set) => ({
  panelOpen: false,
  panelTab: 'chat',
  setPanelTab: (tab) => set({ panelTab: tab, panelOpen: true }),
  togglePanel: () => set((s) => ({ panelOpen: !s.panelOpen })),
  openPanel: (tab) => set((s) => ({ panelOpen: true, panelTab: tab || s.panelTab })),
  closePanel: () => set({ panelOpen: false }),

  privateChatUserId: null,
  privateChatUserName: null,
  openPrivateChat: (userId, userName) => set({ privateChatUserId: userId, privateChatUserName: userName }),
  closePrivateChat: () => set({ privateChatUserId: null, privateChatUserName: null }),

  loading: false,
  loadingText: '',
  setLoading: (loading, text = '') => set({ loading, loadingText: text }),
}))
