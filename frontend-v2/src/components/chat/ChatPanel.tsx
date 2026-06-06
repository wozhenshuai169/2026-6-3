import { useState, useRef, useEffect } from 'react'
import { motion } from 'motion/react'
import { useRoomStore } from '../../stores/roomStore'
import { useUserStore } from '../../stores/userStore'
import { aiAPI } from '../../api/endpoints/ai'
import ChatBubble from './ChatBubble'

export default function ChatPanel() {
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const messages = useRoomStore((s) => s.messages)
  const addMessage = useRoomStore((s) => s.addMessage)
  const user = useUserStore((s) => s.user)
  const roomId = useRoomStore((s) => s.roomId)
  const bottomRef = useRef<HTMLDivElement>(null!)

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const send = async () => {
    const text = input.trim()
    if (!text || !user || !roomId || sending) return
    setInput('')
    setSending(true)
    addMessage({ id: `u_${Date.now()}`, userId: user.userId, userName: user.userName, content: text, type: 'user', timestamp: Date.now() })
    try {
      const res = await aiAPI.publicQuestion({ roomId, userId: user.userId, question: text })
      addMessage({ id: `a_${Date.now()}`, userId: 'ai', userName: '小灵', content: res.answer, type: 'ai', timestamp: Date.now() })
    } catch {
      addMessage({ id: `e_${Date.now()}`, userId: 'system', userName: '', content: '消息发送失败，请重试', type: 'system', timestamp: Date.now() })
    } finally { setSending(false) }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto pb-2 space-y-1">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full gap-3 text-text-muted">
            <span className="text-4xl">💬</span><p className="text-sm">公频暂无消息</p><p className="text-xs">向数字人导游提问吧</p>
          </div>
        )}
        {messages.map((m) => <ChatBubble key={m.id} message={m} isOwn={m.userId === user?.userId} />)}
        <div ref={bottomRef} />
      </div>
      <div className="flex items-center gap-2 pt-2 border-t border-white/5">
        <input value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && send()}
          placeholder="向数字人提问..."
          className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-text-muted focus:outline-none focus:border-accent/40 transition-colors" />
        <motion.button whileTap={{ scale: 0.9 }} onClick={send} disabled={!input.trim() || sending}
          className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-primary to-accent text-white text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed">
          {sending ? '...' : '发送'}
        </motion.button>
      </div>
    </div>
  )
}
