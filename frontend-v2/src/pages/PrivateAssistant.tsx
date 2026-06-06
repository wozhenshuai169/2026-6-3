import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'motion/react'
import { useUserStore } from '../stores/userStore'
import { useRoomStore } from '../stores/roomStore'
import { aiAPI } from '../api/endpoints/ai'
import { roomsAPI } from '../api/endpoints/rooms'
import VoiceButton from '../components/voice/VoiceButton'
import VoiceWaveform from '../components/voice/VoiceWaveform'
import { useVoicePipeline } from '../hooks/useVoicePipeline'
import type { RoomMessage } from '../api/types'

export default function PrivateAssistant() {
  const { roomId } = useParams<{ roomId: string }>()
  const navigate = useNavigate()
  const user = useUserStore((s) => s.user)
  const roomName = useRoomStore((s) => s.roomName)
  const storedRoomId = useRoomStore((s) => s.roomId)
  const setRoom = useRoomStore((s) => s.setRoom)
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [messages, setMessages] = useState<RoomMessage[]>([])
  const bottomRef = useRef<HTMLDivElement>(null!)
  const { state: voiceState, processRecording, startRecording } = useVoicePipeline()

  // 页面刷新时从URL恢复房间数据
  useEffect(() => {
    if (roomId && storedRoomId !== roomId) {
      roomsAPI.getStatus(roomId).then((res) => {
        setRoom({ roomId, members: res.members, currentSpot: res.currentSpot, status: res.status })
      }).catch(() => {})
    }
  }, [roomId, storedRoomId, setRoom])

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages, voiceState.phase])

  const sendText = async () => {
    const text = input.trim()
    if (!text || !user || !roomId || loading) return
    setInput('')
    setLoading(true)
    const userMsg: RoomMessage = { id: `u_${Date.now()}`, userId: user.userId, userName: user.userName, content: text, type: 'user', timestamp: Date.now() }
    setMessages((ms) => [...ms, userMsg])
    try {
      const res = await aiAPI.publicQuestion({ roomId, userId: user.userId, question: text })
      setMessages((ms) => [...ms, { id: `a_${Date.now()}`, userId: 'ai', userName: '小灵', content: res.answer, type: 'ai', timestamp: Date.now() }])
    } catch {
      setMessages((ms) => [...ms, { id: `e_${Date.now()}`, userId: 'system', userName: '', content: '网络错误，请重试', type: 'system', timestamp: Date.now() }])
    } finally { setLoading(false) }
  }

  return (
    <div className="h-full flex flex-col bg-[#0a0a1a]">
      <div className="glass-strong px-4 py-3 flex items-center gap-3 z-10">
        <button onClick={() => navigate(-1)} className="text-text-secondary hover:text-white text-lg">←</button>
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <div className="w-9 h-9 rounded-full flex items-center justify-center text-lg"
            style={{ background: 'radial-gradient(circle, rgba(108,92,231,0.4), rgba(0,210,255,0.2))' }}>🤖</div>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-white truncate">小灵 · 私人导游</p>
            <p className="text-[10px] text-text-muted truncate">{roomName ? `在${roomName}游览中` : '在线'}</p>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-2">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full gap-4 text-text-muted">
            <motion.div animate={{ scale: [1, 1.05, 1] }} transition={{ repeat: Infinity, duration: 2 }}
              className="w-16 h-16 rounded-full flex items-center justify-center"
              style={{ background: 'radial-gradient(circle, rgba(108,92,231,0.25), rgba(0,210,255,0.1))' }}>
              <span className="text-3xl">🤖</span>
            </motion.div>
            <p className="text-sm font-medium">私人AI导游已就绪</p>
            <p className="text-xs">我是你的专属数字人导游"小灵"</p>
            <div className="grid grid-cols-2 gap-2 w-full max-w-xs mt-2">
              {['这里有什么历史故事？', '推荐一条轻松的路线', '最近的卫生间在哪？', '有什么特色拍照点？'].map((q) => (
                <button key={q} onClick={() => setInput(q)}
                  className="text-xs glass rounded-xl px-3 py-2 text-text-secondary hover:text-accent hover:border-accent/20 transition-all text-left">{q}</button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m) => {
          const isOwn = m.userId === user?.userId
          return (
            <div key={m.id} className={`flex ${isOwn ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed ${
                m.type === 'ai' ? 'glass rounded-bl-md' :
                m.type === 'system' ? 'bg-white/5 text-text-muted text-xs mx-auto italic rounded-lg' :
                'bg-primary/20 border border-primary/30 rounded-2xl rounded-br-md'}`}>
                {m.type === 'ai' && <p className="text-[10px] text-accent mb-1">🤖 小灵</p>}
                <p className="text-white break-words">{m.content}</p>
              </div>
            </div>
          )
        })}
        {voiceState.phase !== 'idle' && (
          <div className="flex justify-start">
            <div className="glass rounded-2xl px-4 py-3 max-w-[80%]">
              <div className="flex items-center gap-2">
                <VoiceWaveform active={voiceState.phase !== 'done'} />
                <span className="text-xs text-text-secondary">
                  {voiceState.phase === 'recording' ? '🎤 正在聆听...' :
                   voiceState.phase === 'asr' ? '📝 识别语音...' :
                   voiceState.phase === 'playing' ? '🔊 播放回答...' : '处理中...'}
                </span>
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="glass-strong px-4 py-3 safe-bottom">
        <div className="flex items-center gap-2">
          <VoiceButton onRecordingStart={startRecording} onRecordingStop={processRecording} size="sm" />
          <div className="flex-1 flex items-center gap-2 bg-white/5 border border-white/10 rounded-xl px-3">
            <input value={input} onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && sendText()} placeholder="输入问题..."
              className="flex-1 bg-transparent py-2.5 text-sm text-white placeholder:text-text-muted focus:outline-none" />
            <button onClick={sendText} disabled={!input.trim() || loading}
              className="text-accent hover:text-primary-light disabled:opacity-30 transition-colors">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" /></svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
