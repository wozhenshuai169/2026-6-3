import { motion } from 'motion/react'
import { useRoomStore } from '../../stores/roomStore'
import { useAvatarStore } from '../../stores/avatarStore'

export default function RoomStatus() {
  const roomName = useRoomStore((s) => s.roomName)
  const roomId = useRoomStore((s) => s.roomId)
  const members = useRoomStore((s) => s.members)
  const currentSpot = useRoomStore((s) => s.currentSpot)
  const aiStatus = useAvatarStore((s) => s.aiStatus)

  const shortId = roomId ? roomId.slice(0, 8) : ''

  return (
    <div className="glass-strong px-4 py-2.5 flex items-center justify-between z-30">
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <h2 className="text-sm font-semibold text-white truncate">{roomName || '导览中'}</h2>
          <motion.span animate={{ opacity: [1, 0.4, 1] }} transition={{ repeat: Infinity, duration: 2 }}
            className="w-1.5 h-1.5 rounded-full bg-success flex-shrink-0" />
        </div>
        <p className="text-[11px] text-text-muted truncate">
          {currentSpot ? `📍 ${currentSpot}` : '游览中'} · {members.length}人在线 · <span className="font-mono text-accent">{shortId}</span>
        </p>
      </div>
      <div className="flex items-center gap-2">
        <div className={`glass rounded-full px-2.5 py-1 text-[11px] ${
          aiStatus === 'speaking' ? 'text-success' : aiStatus === 'listening' ? 'text-warning' : aiStatus === 'thinking' ? 'text-warning' : 'text-text-muted'
        }`}>
          {aiStatus === 'speaking' ? '🔊 讲解中' : aiStatus === 'listening' ? '👂 聆听中' : aiStatus === 'thinking' ? '🤔 思考中' : '💤 待命'}
        </div>
        <div className="flex -space-x-1.5">
          {members.slice(0, 3).map((m) => (
            <div key={m.userId} className="w-6 h-6 rounded-full border border-white/10 flex items-center justify-center text-[10px] bg-gradient-to-br from-primary to-accent font-medium" title={m.userName}>
              {m.userName.charAt(0)}
            </div>
          ))}
          {members.length > 3 && (
            <div className="w-6 h-6 rounded-full border border-white/10 flex items-center justify-center text-[10px] bg-white/10 text-text-muted">+{members.length - 3}</div>
          )}
        </div>
      </div>
    </div>
  )
}
