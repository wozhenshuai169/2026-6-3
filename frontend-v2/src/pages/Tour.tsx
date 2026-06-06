import { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { AnimatePresence, motion } from 'motion/react'
import DigitalHumanStage from '../components/digital-human/DigitalHumanStage'
import VoiceButton from '../components/voice/VoiceButton'
import VoiceWaveform from '../components/voice/VoiceWaveform'
import GlassPanel from '../components/shared/GlassPanel'
import RoomStatus from '../components/room/RoomStatus'
import ChatPanel from '../components/chat/ChatPanel'
import MemberList from '../components/chat/MemberList'
import PrivateChat from '../components/chat/PrivateChat'
import RouteCard from '../components/map/RouteCard'
import ScenicMap from '../components/map/ScenicMap'
import { useRoomStore } from '../stores/roomStore'
import { useUserStore } from '../stores/userStore'
import { useUIStore } from '../stores/uiStore'
import { useAvatarStore } from '../stores/avatarStore'
import { useVoicePipeline } from '../hooks/useVoicePipeline'
import { roomsAPI } from '../api/endpoints/rooms'
import { visionAPI } from '../api/endpoints/vision'
import { aiAPI } from '../api/endpoints/ai'

const PANEL_TABS = [
  { key: 'chat', icon: '💬', label: '公频' },
  { key: 'members', icon: '👥', label: '成员' },
  { key: 'assistant', icon: '🤖', label: 'AI助手' },
  { key: 'routes', icon: '🗺️', label: '路线' },
  { key: 'camera', icon: '📷', label: '拍照' },
] as const

export default function Tour() {
  const { roomId } = useParams<{ roomId: string }>()
  const navigate = useNavigate()
  const user = useUserStore((s) => s.user)
  const setRoom = useRoomStore((s) => s.setRoom)
  const storedRoomId = useRoomStore((s) => s.roomId)
  const addMessage = useRoomStore((s) => s.addMessage)
  const setAvatarState = useAvatarStore((s) => s.setState)
  const { panelTab, panelOpen, openPanel, closePanel } = useUIStore()
  const { state: voiceState, processRecording, startRecording } = useVoicePipeline()

  // 页面刷新时恢复房间数据
  useEffect(() => {
    if (roomId && storedRoomId !== roomId) {
      roomsAPI.getStatus(roomId).then((res) => {
        setRoom({ roomId, members: res.members, currentSpot: res.currentSpot, status: res.status })
      }).catch(() => {})
    }
  }, [roomId, storedRoomId, setRoom])

  // 轮询房间状态
  useEffect(() => {
    if (!roomId) return
    const poll = async () => {
      try {
        const res = await roomsAPI.getStatus(roomId)
        setRoom({ roomId, members: res.members, currentSpot: res.currentSpot, status: res.status })
      } catch { /* ignore */ }
    }
    poll()
    const i = setInterval(poll, 5000)
    return () => clearInterval(i)
  }, [roomId, setRoom])

  // 轮询数字人状态
  useEffect(() => {
    if (!roomId) return
    const poll = async () => {
      try {
        const res = await roomsAPI.getAvatarState(roomId)
        setAvatarState(res)
      } catch { /* ignore */ }
    }
    poll()
    const i = setInterval(poll, 3000)
    return () => clearInterval(i)
  }, [roomId, setAvatarState])

  // 语音结果→公频
  useEffect(() => {
    if (voiceState.phase === 'done' && voiceState.answer) {
      addMessage({
        id: `ai_${Date.now()}`, userId: 'ai', userName: '小灵',
        content: voiceState.answer, type: 'ai', timestamp: Date.now(),
      })
      setAvatarState({ aiStatus: 'idle', emotion: 'neutral' })
    }
  }, [voiceState.phase])

  useEffect(() => { if (!user || !roomId) navigate('/', { replace: true }) }, [user, roomId, navigate])
  if (!user || !roomId) return null

  return (
    <div className="h-full flex flex-col relative bg-[#0a0a1a]">
      <RoomStatus />
      <DigitalHumanStage />

      {/* 语音按钮 */}
      <div className="absolute bottom-1/3 left-1/2 -translate-x-1/2 z-30">
        <div className="flex flex-col items-center gap-2">
          {voiceState.phase !== 'idle' && voiceState.phase !== 'recording' && (
            <VoiceWaveform active={voiceState.phase === 'playing'} />
          )}
          <VoiceButton
            onRecordingStart={startRecording}
            onRecordingStop={processRecording}
          />
          {voiceState.asrText && (
            <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }}
              className="text-xs text-text-secondary text-center max-w-[200px] glass rounded-lg px-3 py-1.5">
              "{voiceState.asrText}"
            </motion.p>
          )}
          {voiceState.error && <p className="text-xs text-danger">{voiceState.error}</p>}
        </div>
      </div>

      {/* 功能面板标签栏 */}
      <div className="absolute bottom-20 left-4 right-4 z-30">
        <div className="flex justify-center gap-1">
          {PANEL_TABS.map((tab) => (
            <motion.button key={tab.key} whileTap={{ scale: 0.92 }}
              onClick={() => panelOpen && panelTab === tab.key ? closePanel() : openPanel(tab.key)}
              className={`flex flex-col items-center gap-0.5 px-3 py-2 rounded-xl transition-all duration-200 min-w-[56px] ${
                panelOpen && panelTab === tab.key
                  ? 'glass-strong text-accent scale-105'
                  : 'glass text-text-muted hover:text-text-secondary'
              }`}>
              <span className="text-base">{tab.icon}</span>
              <span className="text-[9px] font-medium">{tab.label}</span>
            </motion.button>
          ))}
        </div>
      </div>

      {/* 功能面板内容 */}
      <AnimatePresence>
        {panelOpen && (
          <GlassPanel open={panelOpen} onClose={closePanel}
            title={PANEL_TABS.find((t) => t.key === panelTab)?.label} height="52vh">
            {panelTab === 'chat' && <ChatPanel />}
            {panelTab === 'members' && <MemberList />}
            {panelTab === 'assistant' && <AssistantPanel roomId={roomId} userId={user.userId} />}
            {panelTab === 'routes' && <RoutePanel />}
            {panelTab === 'camera' && <CameraPanel roomId={roomId} userId={user.userId} />}
          </GlassPanel>
        )}
      </AnimatePresence>

      <PrivateChat />
    </div>
  )
}

/** AI 助手面板 */
function AssistantPanel({ roomId, userId }: { roomId: string; userId: string }) {
  const [q, setQ] = useState('')
  const [answer, setAnswer] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const ask = async () => {
    if (!q.trim()) return
    setLoading(true)
    try {
      const res = await aiAPI.publicQuestion({ roomId, userId, question: q })
      setAnswer(res.answer)
    } catch { setAnswer('抱歉，AI助手暂时无法回应') }
    finally { setLoading(false) }
  }

  return (
    <div className="flex flex-col h-full space-y-3">
      <p className="text-xs text-text-muted">向AI数字人导游提问任何问题</p>
      <div className="flex gap-2">
        <input value={q} onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && ask()}
          placeholder="例如：这座钟楼建于什么年代？"
          className="flex-1 bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-sm text-white placeholder:text-text-muted focus:outline-none focus:border-primary/50" />
        <button onClick={ask} disabled={loading}
          className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-primary to-accent text-white text-sm font-medium disabled:opacity-40">
          {loading ? '...' : '提问'}
        </button>
      </div>
      {answer && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
          className="glass rounded-2xl p-4 text-sm text-text-secondary leading-relaxed">{answer}</motion.div>
      )}
      <button onClick={() => { useUIStore.getState().closePanel(); navigate(`/private/${roomId}`) }}
        className="text-xs text-accent hover:text-primary-light transition-colors self-start">
        → 打开完整AI助手对话
      </button>
    </div>
  )
}

/** 路线面板 */
function RoutePanel() {
  return (
    <div className="space-y-4">
      <ScenicMap />
      <RouteCard />
    </div>
  )
}

/** 拍照面板 */
function CameraPanel({ roomId, userId }: { roomId: string; userId: string }) {
  const [photo, setPhoto] = useState<string | null>(null)
  const [result, setResult] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [mode, setMode] = useState<'idle' | 'preview' | 'result'>('idle')
  const fileRef = useRef<HTMLInputElement>(null!)

  const handleFile = (file: Blob) => {
    const url = URL.createObjectURL(file)
    setPhoto(url)
    setMode('preview')
  }

  const recognize = async () => {
    if (!photo) return
    setLoading(true)
    setMode('result')
    try {
      const res = await visionAPI.recognize({ roomId, userId, imageUrl: photo })
      const desc = res.recognizedSpot?.spotName
        ? `📍 识别到 ${res.recognizedSpot.spotName}（${Math.round(res.recognizedSpot.confidence * 100)}%）\n${res.description}\n\n🏷️ 特征：${res.visualFeatures.join('、')}\n🔗 相关景点：${res.relatedSpots.map((s) => s.spotName).join('、')}`
        : '未能识别到景区地标，请换个角度再试'
      setResult(desc)
    } catch { setResult('识别失败，请重试') }
    finally { setLoading(false) }
  }

  const reset = () => { setMode('idle'); setPhoto(null); setResult(null) }

  return (
    <div className="flex flex-col items-center gap-4">
      {mode === 'idle' && (
        <div className="w-full aspect-[4/3] glass rounded-2xl flex flex-col items-center justify-center gap-3 cursor-pointer"
          onClick={() => fileRef.current?.click()}>
          <span className="text-5xl">📸</span>
          <p className="text-sm text-text-secondary">点击拍照或选择图片</p>
          <p className="text-xs text-text-muted">拍照后AI将识别景点信息</p>
        </div>
      )}
      {mode === 'preview' && photo && (
        <>
          <img src={photo} alt="拍摄的照片" className="w-full aspect-[4/3] object-cover rounded-2xl" />
          <div className="flex gap-3 w-full">
            <button onClick={reset} className="flex-1 py-2.5 rounded-xl bg-white/5 border border-white/10 text-text-secondary text-sm">重拍</button>
            <button onClick={recognize} className="flex-1 py-2.5 rounded-xl bg-gradient-to-r from-primary to-accent text-white text-sm font-medium">🔍 识别景点</button>
          </div>
        </>
      )}
      {mode === 'result' && (
        <>
          {photo && <img src={photo} alt="照片" className="w-full aspect-[4/3] object-cover rounded-2xl opacity-60" />}
          <div className="glass rounded-2xl p-4 w-full">
            {result ? <p className="text-sm text-text-secondary leading-relaxed whitespace-pre-wrap">{result}</p>
              : loading ? <div className="flex items-center gap-3 text-text-muted text-sm"><div className="w-4 h-4 rounded-full border-2 border-accent border-t-transparent animate-spin" />识别中...</div>
              : null}
          </div>
          <button onClick={reset} className="w-full py-2.5 rounded-xl bg-white/5 border border-white/10 text-text-secondary text-sm">再拍一张</button>
        </>
      )}
      <input ref={fileRef} type="file" accept="image/*" capture="environment" className="hidden"
        onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); e.target.value = '' }} />
    </div>
  )
}
