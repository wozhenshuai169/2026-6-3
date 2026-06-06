import { useState, useCallback } from 'react'
import { aiAPI } from '../api/endpoints/ai'
import { useUserStore } from '../stores/userStore'
import { useRoomStore } from '../stores/roomStore'
import { useAvatarStore } from '../stores/avatarStore'

interface VoicePipelineState {
  phase: 'idle' | 'recording' | 'asr' | 'decision' | 'rag' | 'tts' | 'playing' | 'done'
  asrText: string
  answer: string
  audioUrl: string | null
  error: string | null
}

/**
 * 语音全流程: 录音 → ASR → 决策 → RAG → TTS → 播放
 * 后端使用 audioUrl (需公网可访问)，demo 阶段传占位 URL
 */
export function useVoicePipeline() {
  const [state, setState] = useState<VoicePipelineState>({
    phase: 'idle', asrText: '', answer: '', audioUrl: null, error: null,
  })

  const user = useUserStore((s) => s.user)
  const roomId = useRoomStore((s) => s.roomId)
  const setAvatarState = useAvatarStore((s) => s.setState)

  const processRecording = useCallback(async (_audioBlob: Blob) => {
    if (!user || !roomId) return
    setState({ phase: 'asr', asrText: '', answer: '', audioUrl: null, error: null })

    try {
      // Demo阶段使用占位URL — mock provider 不实际访问
      setAvatarState({ aiStatus: 'listening', emotion: 'neutral' })
      setState((s) => ({ ...s, phase: 'decision' }))

      setAvatarState({ aiStatus: 'thinking', emotion: 'thinking' })
      const res = await aiAPI.voiceQuestion({
        roomId,
        userId: user.userId,
        audioUrl: 'https://example.com/audio/demo.wav',
        channel: 'public',
      })

      setState({ phase: 'tts', asrText: res.asrText, answer: res.answer, audioUrl: res.audioUrl, error: null })

      if (res.audioUrl) {
        setState((s) => ({ ...s, phase: 'playing' }))
        setAvatarState({ aiStatus: 'speaking', emotion: 'friendly', text: res.answer, audioUrl: res.audioUrl })
        const audio = new Audio(res.audioUrl)
        await audio.play().catch(() => {})
        if (res.resumeAudioUrl) {
          setAvatarState({ aiStatus: 'resuming' })
          await new Audio(res.resumeAudioUrl).play().catch(() => {})
        }
      }

      setState((s) => ({ ...s, phase: 'done' }))
      setAvatarState({ aiStatus: 'idle', emotion: 'neutral' })
    } catch (err) {
      const msg = err instanceof Error ? err.message : '语音处理失败'
      setState((s) => ({ ...s, phase: 'idle', error: msg }))
      setAvatarState({ aiStatus: 'idle', emotion: 'neutral' })
    }
  }, [user, roomId, setAvatarState])

  const startRecording = useCallback(() => {
    setState({ phase: 'recording', asrText: '', answer: '', audioUrl: null, error: null })
    setAvatarState({ aiStatus: 'listening', emotion: 'neutral' })
  }, [setAvatarState])

  return { state, processRecording, startRecording }
}
