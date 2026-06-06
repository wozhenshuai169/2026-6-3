import { create } from 'zustand'

interface AvatarState {
  aiStatus: string
  emotion: string
  action: string
  text: string
  audioUrl: string | null
  isStreaming: boolean
}

interface AvatarStore extends AvatarState {
  setState: (s: Partial<AvatarState>) => void
  reset: () => void
}

const initial: AvatarState = {
  aiStatus: 'idle',
  emotion: 'neutral',
  action: '',
  text: '',
  audioUrl: null,
  isStreaming: false,
}

export const useAvatarStore = create<AvatarStore>((set) => ({
  ...initial,
  setState: (s) => set((prev) => ({ ...prev, ...s })),
  reset: () => set(initial),
}))
