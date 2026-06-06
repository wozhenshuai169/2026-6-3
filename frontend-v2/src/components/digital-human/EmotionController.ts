export interface EmotionColors {
  primary: string
  accent: string
  glow: string
  particleSpeed: number
  haloRadius: number
}

const palettes: Record<string, EmotionColors> = {
  friendly: {
    primary: '#a29bfe', accent: '#00D2FF', glow: 'rgba(108, 92, 231, 0.4)',
    particleSpeed: 0.3, haloRadius: 1.0,
  },
  neutral: {
    primary: '#6C5CE7', accent: '#00D2FF', glow: 'rgba(0, 210, 255, 0.3)',
    particleSpeed: 0.2, haloRadius: 1.0,
  },
  thinking: {
    primary: '#FFD43B', accent: '#FF922B', glow: 'rgba(255, 212, 59, 0.35)',
    particleSpeed: 0.6, haloRadius: 1.15,
  },
  surprised: {
    primary: '#FF6B6B', accent: '#FFD43B', glow: 'rgba(255, 107, 107, 0.5)',
    particleSpeed: 0.8, haloRadius: 1.3,
  },
}

const statusSpeeds: Record<string, number> = {
  idle: 0.15, listening: 0.5, speaking: 0.35,
  thinking: 0.7, paused: 0.05, resuming: 0.25,
}

export function getEmotionColors(emotion: string): EmotionColors {
  return palettes[emotion] || palettes.neutral
}

export function getStatusSpeed(status: string): number {
  return statusSpeeds[status] || 0.15
}
