import { motion } from 'motion/react'
import { useRoomStore } from '../../stores/roomStore'
import { useUserStore } from '../../stores/userStore'
import { useUIStore } from '../../stores/uiStore'

export default function MemberList() {
  const members = useRoomStore((s) => s.members)
  const leaderId = useRoomStore((s) => s.leaderId)
  const currentUser = useUserStore((s) => s.user)
  const openPrivateChat = useUIStore((s) => s.openPrivateChat)

  if (members.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-3 text-text-muted">
        <span className="text-4xl">👥</span><p className="text-sm">暂无成员</p>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {members.map((m) => {
        const isMe = m.userId === currentUser?.userId
        const isLeader = m.userId === leaderId

        return (
          <motion.div key={m.userId} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }}
            className="flex items-center gap-3 glass rounded-xl px-4 py-3">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center text-lg ${
              isLeader ? 'bg-gradient-to-br from-warning to-danger' : 'bg-gradient-to-br from-primary to-accent'
            }`}>
              {isLeader ? '👑' : m.userName.charAt(0)}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">
                {m.userName}{isMe && <span className="text-text-muted ml-1">(我)</span>}
              </p>
              <p className="text-xs text-text-muted">{isLeader ? '团长' : '游客'}</p>
            </div>
            {!isMe && (
              <motion.button whileTap={{ scale: 0.9 }} onClick={() => openPrivateChat(m.userId, m.userName)}
                className="px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-xs text-text-secondary hover:text-accent hover:border-accent/30 transition-all">
                💬 私聊
              </motion.button>
            )}
          </motion.div>
        )
      })}
    </div>
  )
}
