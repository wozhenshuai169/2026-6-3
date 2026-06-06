import { useState, useRef, useCallback } from 'react'
import { motion } from 'motion/react'

interface VoiceButtonProps {
  onRecordingStart: () => void
  onRecordingStop: (audioBlob: Blob) => void
  disabled?: boolean
  size?: 'sm' | 'lg'
}

export default function VoiceButton({ onRecordingStart, onRecordingStop, disabled, size = 'lg' }: VoiceButtonProps) {
  const [recording, setRecording] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const mediaRecorder = useRef<MediaRecorder | null>(null)
  const chunks = useRef<Blob[]>([])

  const startRecording = useCallback(async () => {
    setError(null)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' })
      mediaRecorder.current = recorder
      chunks.current = []

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunks.current.push(e.data)
      }

      recorder.onstop = () => {
        const blob = new Blob(chunks.current, { type: 'audio/webm' })
        stream.getTracks().forEach((t) => t.stop())
        onRecordingStop(blob)
      }

      recorder.start()
      setRecording(true)
      onRecordingStart()
    } catch {
      setError('无法访问麦克风')
    }
  }, [onRecordingStart, onRecordingStop])

  const stopRecording = useCallback(() => {
    if (mediaRecorder.current && mediaRecorder.current.state === 'recording') {
      mediaRecorder.current.stop()
    }
    setRecording(false)
  }, [])

  const sizeClass = size === 'lg' ? 'w-20 h-20' : 'w-14 h-14'
  const innerSize = size === 'lg' ? 'w-14 h-14' : 'w-10 h-10'

  return (
    <div className="flex flex-col items-center gap-3">
      {error && <p className="text-danger text-xs">{error}</p>}

      {/* 外层脉冲环 */}
      {recording && (
        <motion.div
          className={`absolute ${sizeClass} rounded-full border-2 border-danger/40`}
          initial={{ scale: 1, opacity: 0.6 }}
          animate={{ scale: 1.5, opacity: 0 }}
          transition={{ repeat: Infinity, duration: 1.2 }}
        />
      )}

      <motion.button
        onClick={recording ? stopRecording : startRecording}
        disabled={disabled}
        whileTap={{ scale: 0.92 }}
        className={`relative ${sizeClass} rounded-full flex items-center justify-center transition-all duration-300 ${
          recording
            ? 'bg-danger/20 border-2 border-danger shadow-[0_0_30px_rgba(255,107,107,0.3)]'
            : 'bg-white/5 border border-white/10 hover:bg-white/10 hover:border-accent/30'
        } ${disabled ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer'}`}
      >
        <div className={`${innerSize} rounded-full flex items-center justify-center ${
          recording ? 'bg-danger' : 'bg-gradient-to-br from-primary to-accent'
        }`}>
          {/* 麦克风图标 */}
          <svg
            viewBox="0 0 24 24"
            className={size === 'lg' ? 'w-7 h-7' : 'w-5 h-5'}
            fill="none"
            stroke="white"
            strokeWidth={2}
            strokeLinecap="round"
          >
            {recording ? (
              <>
                <rect x="8" y="8" width="8" height="8" rx="1" />
                <line x1="12" y1="18" x2="12" y2="22" />
              </>
            ) : (
              <>
                <path d="M12 2a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z" />
                <path d="M19 10v1a7 7 0 0 1-14 0v-1" />
                <line x1="12" y1="18" x2="12" y2="22" />
              </>
            )}
          </svg>
        </div>
      </motion.button>

      <span className={`text-xs transition-colors ${recording ? 'text-danger font-medium' : 'text-text-muted'}`}>
        {recording ? '松开发送' : disabled ? '未就绪' : '按住说话'}
      </span>
    </div>
  )
}
