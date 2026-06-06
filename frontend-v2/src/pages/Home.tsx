import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'motion/react'
import { useUserStore } from '../stores/userStore'
import { useRoomStore } from '../stores/roomStore'
import { authAPI } from '../api/endpoints/auth'
import { roomsAPI } from '../api/endpoints/rooms'

export default function Home() {
  const navigate = useNavigate()
  const { user, setUser } = useUserStore()
  const setRoom = useRoomStore((s) => s.setRoom)

  const [name, setName] = useState('')
  const [roomIdInput, setRoomIdInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [step, setStep] = useState<'login' | 'join'>('login')

  const handleLogin = async () => {
    const trimmed = name.trim()
    if (!trimmed) return setError('请输入昵称')
    setLoading(true)
    setError('')
    try {
      const res = await authAPI.register({ userName: trimmed, password: '123456' })
      setUser({ userId: res.userId, userName: res.userName, token: res.token })
      setStep('join')
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '注册失败'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  const handleJoin = async () => {
    const id = roomIdInput.trim()
    if (!id || !user) return setError('请输入房间ID')
    setLoading(true)
    setError('')
    try {
      await roomsAPI.join(id, { token: user.token })
      const status = await roomsAPI.getStatus(id)
      setRoom({
        roomId: id,
        members: status.members,
        currentSpot: status.currentSpot,
        status: status.status,
      })
      navigate(`/tour/${id}`)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '加入失败'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async () => {
    if (!user) return setError('请先输入昵称')
    setLoading(true)
    setError('')
    try {
      const res = await roomsAPI.create({
        token: user.token,
        roomName: `${user.userName}的导览团`,
        scenicAreaId: 'area_001',
        routeId: 'route_001',
      })
      const status = await roomsAPI.getStatus(res.roomId)
      setRoom({
        roomId: res.roomId,
        roomName: `${user.userName}的导览团`,
        members: status.members,
        currentSpot: status.currentSpot,
        status: status.status,
      })
      navigate(`/tour/${res.roomId}`)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '创建失败'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="h-full flex flex-col items-center justify-center px-6 relative overflow-hidden">
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/4 -left-16 w-64 h-64 rounded-full bg-primary/10 blur-3xl" />
        <div className="absolute bottom-1/4 -right-16 w-64 h-64 rounded-full bg-accent/10 blur-3xl" />
      </div>

      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-10">
        <div className="w-20 h-20 mx-auto mb-4 rounded-full flex items-center justify-center"
          style={{ background: 'radial-gradient(circle, rgba(108,92,231,0.3), rgba(0,210,255,0.1))' }}>
          <span className="text-4xl">🧭</span>
        </div>
        <h1 className="text-3xl font-bold text-gradient mb-2">灵境同行</h1>
        <p className="text-text-secondary text-sm">AI数字人 · 智慧景区导览</p>
      </motion.div>

      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }} className="w-full max-w-sm space-y-4">
        {step === 'login' ? (
          <>
            <div>
              <label className="text-xs text-text-secondary mb-1.5 block">你的昵称</label>
              <input
                value={name} onChange={(e) => setName(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleLogin()}
                placeholder="输入昵称..." autoFocus
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-text-muted focus:outline-none focus:border-primary/50 transition-all text-center"
              />
            </div>
            <motion.button whileTap={{ scale: 0.97 }} onClick={handleLogin} disabled={loading}
              className="w-full py-3.5 rounded-xl bg-gradient-to-r from-primary to-accent text-white font-semibold text-base disabled:opacity-50">
              {loading ? '...' : '进入导览'}
            </motion.button>
          </>
        ) : (
          <>
            <div className="text-center mb-2">
              <span className="text-sm text-text-secondary">你好，</span>
              <span className="text-sm text-white font-semibold">{user?.userName}</span>
            </div>
            <div>
              <label className="text-xs text-text-secondary mb-1.5 block">输入房间ID加入（团长分享的ID）</label>
              <input
                value={roomIdInput} onChange={(e) => setRoomIdInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleJoin()}
                placeholder="输入房间ID..."
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-text-muted focus:outline-none focus:border-accent/50 transition-all text-center text-sm font-mono"
                autoFocus
              />
            </div>
            <div className="flex gap-3">
              <motion.button whileTap={{ scale: 0.97 }} onClick={handleJoin} disabled={loading || !roomIdInput.trim()}
                className="flex-1 py-3.5 rounded-xl bg-accent/20 border border-accent/30 text-accent font-semibold text-sm disabled:opacity-40">
                加入房间
              </motion.button>
              <motion.button whileTap={{ scale: 0.97 }} onClick={handleCreate} disabled={loading}
                className="flex-1 py-3.5 rounded-xl bg-gradient-to-r from-primary to-accent text-white font-semibold text-sm disabled:opacity-40">
                创建房间
              </motion.button>
            </div>
            <button onClick={() => setStep('login')} className="w-full text-xs text-text-muted hover:text-text-secondary transition-colors">
              ← 更换昵称
            </button>
          </>
        )}
        {error && (
          <motion.p initial={{ opacity: 0, y: -5 }} animate={{ opacity: 1, y: 0 }} className="text-xs text-danger text-center">
            {error}
          </motion.p>
        )}
      </motion.div>

      {/* 角色入口 */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}
        className="absolute bottom-8 left-6 right-6 flex gap-3">
        <button onClick={() => { if (!user) { setError('请先输入昵称'); return }; navigate('/guide') }}
          className="flex-1 py-3 rounded-xl bg-white/5 border border-white/8 text-text-secondary hover:text-white hover:border-white/15 transition-all text-sm">
          🎯 团长端
        </button>
        <button onClick={() => navigate('/admin')}
          className="flex-1 py-3 rounded-xl bg-white/5 border border-white/8 text-text-secondary hover:text-white hover:border-white/15 transition-all text-sm">
          📊 管理后台
        </button>
      </motion.div>
    </div>
  )
}
