import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'motion/react'
import { useUIStore } from '../../stores/uiStore'
import { useUserStore } from '../../stores/userStore'
import { useChatStore } from '../../stores/chatStore'
import type { PrivateMessage } from '../../api/types'

export default function PrivateChat() {
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null!)
  const privateChatUserId = useUIStore((s) => s.privateChatUserId)
  const privateChatUserName = useUIStore((s) => s.privateChatUserName)
  const closePrivateChat = useUIStore((s) => s.closePrivateChat)
  const user = useUserStore((s) => s.user)
  const privateChats = useChatStore((s) => s.privateChats)
  const addPrivateMessage = useChatStore((s) => s.addPrivateMessage)

  const open = !!privateChatUserId
  const partnerId = privateChatUserId || ''
  const messages = privateChats[partnerId] || []

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = () => {
    const text = input.trim()
    if (!text || !user || !privateChatUserId) return
    const msg: PrivateMessage = {
      id: `pm_${Date.now()}`,
      fromUserId: user.userId,
      fromUserName: user.userName,
      toUserId: privateChatUserId,
      content: text,
      timestamp: Date.now(),
    }
    addPrivateMessage(msg)
    setInput('')
  }

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ x: '100%' }}
          animate={{ x: 0 }}
          exit={{ x: '100%' }}
          transition={{ type: 'spring', damping: 25, stiffness: 200 }}
          className="absolute inset-0 z-50 glass-strong flex flex-col"
        >
          {/* Header */}
          <div className="flex items-center gap-3 px-4 py-3 border-b border-white/5">
            <button onClick={closePrivateChat} className="text-text-secondary hover:text-white text-lg">
              ←
            </button>
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center text-sm">
              {privateChatUserName?.charAt(0)}
            </div>
            <div>
              <p className="text-sm font-medium">{privateChatUserName}</p>
              <p className="text-[10px] text-text-muted">私聊中</p>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-3 py-2 space-y-2">
            {messages.length === 0 && (
              <p className="text-text-muted text-xs text-center mt-8">开始聊天吧</p>
            )}
            {messages.map((m) => {
              const isMine = m.fromUserId === user?.userId
              return (
                <div key={m.id} className={`flex ${isMine ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[75%] px-3 py-2 rounded-2xl text-sm ${
                    isMine
                      ? 'bg-primary/20 border border-primary/30 rounded-br-md'
                      : 'glass rounded-bl-md'
                  }`}>
                    <p className="text-white">{m.content}</p>
                    <p className="text-[10px] text-text-muted mt-0.5 text-right">
                      {new Date(m.timestamp).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                </div>
              )
            })}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div className="flex items-center gap-2 p-3 border-t border-white/5 safe-bottom">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && send()}
              placeholder="输入消息..."
              className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-text-muted focus:outline-none focus:border-accent/40"
            />
            <button
              onClick={send}
              disabled={!input.trim()}
              className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-primary to-accent text-white text-sm font-medium disabled:opacity-40"
            >
              发送
            </button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
