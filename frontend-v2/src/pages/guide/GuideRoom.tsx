import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'motion/react'
import { useUserStore } from '../../stores/userStore'
import { useRoomStore } from '../../stores/roomStore'
import { useAvatarStore } from '../../stores/avatarStore'
import { roomsAPI } from '../../api/endpoints/rooms'
import { aiAPI } from '../../api/endpoints/ai'
import ScenicMap from '../../components/map/ScenicMap'

const SPOTS = [
  { id: 'main_hall', name: '大殿', icon: '🏛️', desc: '灵境古苑主殿，建于清代乾隆年间' },
  { id: 'bell_tower', name: '钟楼', icon: '🔔', desc: '明代青铜钟，重达三吨' },
  { id: 'drum_tower', name: '鼓楼', icon: '🥁', desc: '古时报时所用，晨钟暮鼓' },
  { id: 'courtyard', name: '中庭', icon: '🌳', desc: '百年古树参天，四季皆景' },
  { id: 'gallery', name: '石雕长廊', icon: '🗿', desc: '展现历代工匠精湛石雕技艺' },
  { id: 'service', name: '服务中心', icon: '🏪', desc: '游客休憩与咨询服务' },
  { id: 'east_gate', name: '东门', icon: '⛩️', desc: '景区主入口，明代建筑风格' },
]

export default function GuideRoom() {
  const { roomId } = useParams<{ roomId: string }>()
  const navigate = useNavigate()
  const user = useUserStore((s) => s.user)
  const { roomName, members, currentSpot, leaderId, setRoom, setCurrentSpot, addMessage } = useRoomStore()
  const { setState: setAvatarState } = useAvatarStore()
  const [spotSelectOpen, setSpotSelectOpen] = useState(false)
  const [triggerLoading, setTriggerLoading] = useState(false)
  const [broadcastText, setBroadcastText] = useState('')

  useEffect(() => {
    if (!roomId) return
    const poll = async () => {
      try {
        const res = await roomsAPI.getStatus(roomId)
        setRoom({ roomId, members: res.members, currentSpot: res.currentSpot, status: res.status })
      } catch { /* ignore */ }
    }
    poll()
    const i = setInterval(poll, 4000)
    return () => clearInterval(i)
  }, [roomId, setRoom])

  const switchSpot = async (spotId: string, spotName: string) => {
    if (!roomId) return
    setCurrentSpot(spotName)
    setSpotSelectOpen(false)
    try { await roomsAPI.updateSpot(roomId, { spotId }) } catch { /* ignore */ }
    addMessage({ id: `sys_${Date.now()}`, userId: 'system', userName: '', content: `📍 团长切换景点至：${spotName}`, type: 'system', timestamp: Date.now() })
  }

  const triggerExplanation = async () => {
    if (!user || !roomId || !currentSpot) return
    setTriggerLoading(true)
    try {
      const res = await aiAPI.publicQuestion({ roomId, userId: user.userId, question: `请为大家详细讲解${currentSpot}的历史、特色和文化故事` })
      addMessage({ id: `ai_${Date.now()}`, userId: 'ai', userName: '小灵', content: res.answer, type: 'ai', timestamp: Date.now() })
      setAvatarState({ aiStatus: 'speaking', emotion: 'friendly', text: res.answer })
    } catch { /* ignore */ }
    finally { setTriggerLoading(false) }
  }

  const sendBroadcast = () => {
    if (!broadcastText.trim()) return
    addMessage({ id: `sys_${Date.now()}`, userId: 'system', userName: '', content: `📢 团长广播：${broadcastText.trim()}`, type: 'system', timestamp: Date.now() })
    setBroadcastText('')
  }

  const currentSpotData = SPOTS.find((s) => s.id === currentSpot || s.name === currentSpot)

  return (
    <div className="h-full flex flex-col bg-[#0a0a1a]">
      <div className="glass-strong px-4 py-3 flex items-center gap-3">
        <button onClick={() => navigate('/guide')} className="text-text-secondary hover:text-white text-lg">←</button>
        <div className="flex-1 min-w-0">
          <h1 className="text-sm font-bold text-white truncate">{roomName || '导览控制'}</h1>
          <p className="text-[10px] text-text-muted">{roomId?.slice(0, 8)} · {members.length}人 · {currentSpot || '未开始'}</p>
        </div>
        <div className="w-2 h-2 rounded-full bg-success animate-pulse" />
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-3">
        <div className="glass rounded-2xl p-4">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-white">📍 当前景点</h2>
            <button onClick={() => setSpotSelectOpen(!spotSelectOpen)}
              className="text-xs px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-text-secondary hover:text-accent hover:border-accent/30 transition-all">切换景点</button>
          </div>
          {currentSpotData ? (
            <div className="flex items-start gap-3">
              <span className="text-3xl">{currentSpotData.icon}</span>
              <div><p className="text-base font-bold text-white">{currentSpotData.name}</p>
                <p className="text-xs text-text-secondary mt-1">{currentSpotData.desc}</p></div>
            </div>
          ) : <p className="text-text-muted text-sm text-center py-4">尚未设置当前景点</p>}
          <AnimatePresence>
            {spotSelectOpen && (
              <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className="overflow-hidden">
                <div className="grid grid-cols-2 gap-2 mt-3 pt-3 border-t border-white/5">
                  {SPOTS.map((spot) => (
                    <button key={spot.id} onClick={() => switchSpot(spot.id, spot.name)}
                      className={`text-left px-3 py-2.5 rounded-xl text-xs transition-all ${
                        (spot.id === currentSpot || spot.name === currentSpot)
                          ? 'bg-primary/20 border border-primary/40 text-primary-light'
                          : 'bg-white/5 border border-white/8 text-text-secondary hover:border-white/15'
                      }`}><span className="mr-1.5">{spot.icon}</span>{spot.name}</button>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <div className="glass rounded-2xl p-4">
          <h2 className="text-sm font-semibold text-white mb-3">🎮 导览控制</h2>
          <div className="grid grid-cols-2 gap-3">
            <motion.button whileTap={{ scale: 0.95 }} onClick={triggerExplanation} disabled={triggerLoading || !currentSpot}
              className="p-4 rounded-xl bg-gradient-to-br from-primary/20 to-accent/10 border border-primary/20 text-center disabled:opacity-40">
              <span className="text-2xl">🔊</span>
              <p className="text-sm text-white font-medium mt-1">{triggerLoading ? '触发中...' : '触发讲解'}</p>
              <p className="text-[10px] text-text-muted mt-0.5">AI自动讲解当前景点</p>
            </motion.button>
            <motion.button whileTap={{ scale: 0.95 }}
              onClick={() => setAvatarState({ aiStatus: 'idle', emotion: 'neutral' })}
              className="p-4 rounded-xl bg-white/5 border border-white/10 text-center hover:border-white/20 transition-all">
              <span className="text-2xl">⏸️</span>
              <p className="text-sm text-white font-medium mt-1">暂停/继续</p>
              <p className="text-[10px] text-text-muted mt-0.5">控制AI讲解状态</p>
            </motion.button>
          </div>
          <div className="mt-3 flex gap-2">
            <input value={broadcastText} onChange={(e) => setBroadcastText(e.target.value)}
              placeholder="发送广播消息..." onKeyDown={(e) => e.key === 'Enter' && sendBroadcast()}
              className="flex-1 bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-xs text-white placeholder:text-text-muted focus:outline-none focus:border-accent/50" />
            <button onClick={sendBroadcast} disabled={!broadcastText.trim()}
              className="px-4 py-2.5 rounded-xl bg-accent/20 border border-accent/30 text-accent text-xs font-medium disabled:opacity-30">广播</button>
          </div>
        </div>

        <div className="glass rounded-2xl p-4">
          <h2 className="text-sm font-semibold text-white mb-3">🗺️ 景区地图</h2>
          <ScenicMap />
        </div>

        <div className="glass rounded-2xl p-4">
          <h2 className="text-sm font-semibold text-white mb-3">👥 团成员 ({members.length}人)</h2>
          {members.length === 0 ? <p className="text-text-muted text-xs text-center py-4">暂无成员加入</p> : (
            <div className="space-y-2">
              {members.map((m) => (
                <div key={m.userId} className="flex items-center gap-3 bg-white/5 rounded-xl px-3 py-2.5">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm ${
                    m.userId === leaderId ? 'bg-gradient-to-br from-warning to-danger' : 'bg-gradient-to-br from-primary to-accent'
                  }`}>
                    {m.userId === leaderId ? '👑' : m.userName.charAt(0)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-white truncate">{m.userName}</p>
                    <p className="text-[10px] text-text-muted">{m.userId === leaderId ? '团长' : '游客'}</p>
                  </div>
                  <span className={`w-1.5 h-1.5 rounded-full ${m.userId === leaderId ? 'bg-warning' : 'bg-success'}`} />
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
