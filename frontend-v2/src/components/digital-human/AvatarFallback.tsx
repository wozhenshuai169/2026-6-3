import { motion } from 'motion/react'
import { useAvatarStore } from '../../stores/avatarStore'

const emotionIcons: Record<string, string> = {
  friendly: '😊',
  neutral: '😐',
  thinking: '🤔',
  surprised: '😮',
}

const statusPulse: Record<string, number> = {
  idle: 1,
  listening: 1.15,
  speaking: 1.08,
  thinking: 1.12,
  paused: 0.95,
  resuming: 1.05,
}

export default function AvatarFallback() {
  const { emotion, aiStatus, text } = useAvatarStore()
  const scale = statusPulse[aiStatus] || 1

  return (
    <div className="relative w-full flex-1 min-h-0 flex flex-col items-center justify-center">
      {/* 圆形 UI 数字人 */}
      <motion.div
        animate={{ scale }}
        transition={{ type: 'spring', damping: 15, stiffness: 120 }}
        className="relative w-48 h-48 rounded-full flex items-center justify-center glow-border"
        style={{
          background: 'radial-gradient(circle at 40% 35%, rgba(108,92,231,0.25), rgba(0,210,255,0.1), transparent 70%)',
        }}
      >
        {/* 外层旋转环 */}
        <motion.div
          className="absolute inset-0 rounded-full border border-accent/20"
          animate={{ rotate: 360 }}
          transition={{ repeat: Infinity, duration: 8, ease: 'linear' }}
        />

        {/* 中层虚线环 */}
        <motion.div
          className="absolute inset-2 rounded-full border border-dashed border-primary-light/15"
          animate={{ rotate: -360 }}
          transition={{ repeat: Infinity, duration: 12, ease: 'linear' }}
        />

        {/* 表情图标 */}
        <motion.span
          className="text-7xl relative z-10"
          animate={{ scale: [1, 1.03, 1] }}
          transition={{ repeat: Infinity, duration: 2, ease: 'easeInOut' }}
        >
          {emotionIcons[emotion] || '😊'}
        </motion.span>

        {/* 底部光晕 */}
        <div className="absolute bottom-4 w-32 h-1 rounded-full bg-gradient-to-r from-transparent via-accent/40 to-transparent blur-sm" />
      </motion.div>

      {/* AI 文字 */}
      {text && (
        <motion.p
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-6 px-6 py-3 glass rounded-2xl text-sm text-text-secondary text-center max-w-[280px]"
        >
          {text}
        </motion.p>
      )}
    </div>
  )
}
