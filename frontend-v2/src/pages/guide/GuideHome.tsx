import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'motion/react'
import { useUserStore } from '../../stores/userStore'
import { useRoomStore } from '../../stores/roomStore'
import { roomsAPI } from '../../api/endpoints/rooms'

interface GuideRoom {
  roomId: string
  roomName: string
  memberCount: number
  currentSpot: string
  status: string
}

export default function GuideHome() {
  const navigate = useNavigate()
  const user = useUserStore((s) => s.user)
  const setRoom = useRoomStore((s) => s.setRoom)
  const [rooms] = useState<GuideRoom[]>([])
  const [loading, setLoading] = useState(false)
  const [roomName, setRoomName] = useState('')
  const [showCreate, setShowCreate] = useState(false)

  const handleCreate = async () => {
    if (!user || !roomName.trim()) return
    setLoading(true)
    try {
      const res = await roomsAPI.create({
        token: user.token, roomName: roomName.trim(),
        scenicAreaId: 'area_001', routeId: 'route_001',
      })
      setRoom({
        roomId: res.roomId, roomName: roomName.trim(),
        leaderId: user.userId,
        members: [], currentSpot: '', status: 'created',
      })
      setShowCreate(false)
      setRoomName('')
      navigate(`/guide/${res.roomId}`)
    } catch { /* ignore */ }
    finally { setLoading(false) }
  }

  const enterRoom = async (room: GuideRoom) => {
    try {
      const status = await roomsAPI.getStatus(room.roomId)
      setRoom({
        roomId: room.roomId, roomName: room.roomName,
        leaderId: user?.userId,
        members: status.members, currentSpot: status.currentSpot, status: status.status,
      })
    } catch { /* ignore */ }
    navigate(`/guide/${room.roomId}`)
  }

  return (
    <div className="h-full flex flex-col bg-[#0a0a1a]">
      <div className="glass-strong px-5 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-white">🎯 团长控制台</h1>
          <p className="text-xs text-text-muted mt-0.5">{user?.userName}，管理你的导览团</p>
        </div>
        <button onClick={() => navigate('/')} className="text-text-muted hover:text-white text-xl">🏠</button>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        <div className="glass rounded-2xl p-5 space-y-3">
          <h2 className="text-sm font-semibold text-white">快捷操作</h2>
          <div className="grid grid-cols-2 gap-3">
            <motion.button whileTap={{ scale: 0.96 }} onClick={() => setShowCreate(!showCreate)}
              className="p-4 rounded-xl bg-gradient-to-br from-primary/20 to-accent/10 border border-primary/20 text-left hover:border-primary/40 transition-all">
              <span className="text-2xl">🚩</span>
              <p className="text-sm text-white font-medium mt-2">创建新团</p>
              <p className="text-[10px] text-text-muted mt-0.5">开始新的导览</p>
            </motion.button>
            <motion.button whileTap={{ scale: 0.96 }} onClick={() => navigate('/guide/routes')}
              className="p-4 rounded-xl bg-white/5 border border-white/8 text-left hover:border-white/15 transition-all">
              <span className="text-2xl">🗺️</span>
              <p className="text-sm text-white font-medium mt-2">路线管理</p>
              <p className="text-[10px] text-text-muted mt-0.5">查看和配置路线</p>
            </motion.button>
          </div>
          {showCreate && (
            <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} className="space-y-2 pt-2">
              <input value={roomName} onChange={(e) => setRoomName(e.target.value)}
                placeholder="输入导览团名称..." onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder:text-text-muted focus:outline-none focus:border-primary/50" autoFocus />
              <div className="flex gap-2">
                <button onClick={() => setShowCreate(false)} className="flex-1 py-2.5 rounded-xl bg-white/5 text-text-secondary text-sm">取消</button>
                <button onClick={handleCreate} disabled={loading} className="flex-1 py-2.5 rounded-xl bg-gradient-to-r from-primary to-accent text-white text-sm font-medium disabled:opacity-40">
                  {loading ? '创建中...' : '确认创建'}
                </button>
              </div>
            </motion.div>
          )}
        </div>

        <div>
          <h2 className="text-sm font-semibold text-white mb-3">进行中的导览团</h2>
          {rooms.length === 0 ? (
            <div className="glass rounded-2xl p-8 text-center">
              <span className="text-4xl">📭</span>
              <p className="text-text-secondary text-sm mt-3">暂无进行中的导览团</p>
              <p className="text-text-muted text-xs mt-1">创建一个新的导览团开始吧</p>
            </div>
          ) : (
            <div className="space-y-2">
              {rooms.map((room) => (
                <motion.div key={room.roomId} whileTap={{ scale: 0.98 }} onClick={() => enterRoom(room)}
                  className="glass rounded-xl p-4 cursor-pointer hover:border-accent/20 transition-all">
                  <div className="flex items-center justify-between">
                    <div className="min-w-0 flex-1">
                      <h3 className="text-sm font-semibold text-white truncate">{room.roomName}</h3>
                      <div className="flex items-center gap-3 mt-1.5">
                        <span className="text-xs text-text-muted">ID: <span className="text-accent font-mono">{room.roomId.slice(0, 8)}</span></span>
                        <span className="text-xs text-text-muted">👥 {room.memberCount}人</span>
                        <span className="text-xs text-text-muted">📍 {room.currentSpot || '未开始'}</span>
                      </div>
                    </div>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full ${room.status === 'active' ? 'bg-success/20 text-success' : 'bg-white/10 text-text-muted'}`}>
                      {room.status === 'active' ? '进行中' : '已结束'}
                    </span>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
