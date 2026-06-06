import { motion } from 'motion/react'
import type { RoomMessage } from '../../api/types'

interface Props {
  message: RoomMessage
  isOwn: boolean
}

export default function ChatBubble({ message, isOwn }: Props) {
  const bubbleClass = message.type === 'system'
    ? 'bg-white/5 text-text-muted text-xs mx-auto italic max-w-[70%]'
    : message.type === 'ai'
      ? 'glass rounded-2xl rounded-bl-md text-text-primary'
      : isOwn
        ? 'bg-primary/20 border border-primary/30 rounded-2xl rounded-br-md text-text-primary'
        : 'glass rounded-2xl rounded-bl-md text-text-primary'

  const alignClass = message.type === 'system'
    ? 'justify-center'
    : message.type === 'ai' || !isOwn
      ? 'justify-start'
      : 'justify-end'

  return (
    <motion.div
      initial={{ opacity: 0, y: 12, scale: 0.96 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      className={`flex ${alignClass} mb-2 px-1`}
    >
      <div className={`max-w-[80%] px-3.5 py-2.5 ${bubbleClass}`}>
        {message.type !== 'system' && (
          <p className="text-[10px] text-text-muted mb-1 font-medium">
            {message.type === 'ai' ? '🤖 小灵' : message.userName}
          </p>
        )}
        <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">
          {message.content}
        </p>
        <p className="text-[10px] text-text-muted mt-1 text-right">
          {formatTime(message.timestamp)}
        </p>
      </div>
    </motion.div>
  )
}

function formatTime(ts: number) {
  const d = new Date(ts)
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
