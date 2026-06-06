import { useState } from 'react'
import { motion } from 'motion/react'
import { useUserStore } from '../../stores/userStore'
import { useRoomStore } from '../../stores/roomStore'
import { recommendAPI } from '../../api/endpoints/recommend'
import type { RoutePreferences, RouteRecommendResponse } from '../../api/types'

const INTEREST_OPTIONS = [
  { key: 'history', label: '🏛️ 历史文化' },
  { key: 'architecture', label: '🏗️ 建筑艺术' },
  { key: 'nature', label: '🌿 自然风光' },
  { key: 'photography', label: '📸 摄影打卡' },
  { key: 'food', label: '🍜 美食特产' },
  { key: 'story', label: '📖 民间故事' },
]

const STRENGTH_LABELS: Record<string, string> = { low: '轻松', medium: '适中', high: '挑战' }

export default function RouteCard() {
  const [prefs, setPrefs] = useState<RoutePreferences>({
    interest: [], timeLimit: 60, physicalStrength: 'medium',
    withChildren: false, withElderly: false, avoidCrowd: true,
  })
  const [result, setResult] = useState<RouteRecommendResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const user = useUserStore((s) => s.user)
  const roomId = useRoomStore((s) => s.roomId)

  const toggle = (key: string) => setPrefs((p) => ({
    ...p, interest: p.interest.includes(key) ? p.interest.filter((i) => i !== key) : [...p.interest, key],
  }))

  const recommend = async () => {
    if (!user || !roomId) return
    setLoading(true)
    try {
      const res = await recommendAPI.getRoute({ roomId, userId: user.userId, preferences: prefs })
      setResult(res)
    } catch { /* ignore */ }
    finally { setLoading(false) }
  }

  const strengthKeys = ['low', 'medium', 'high'] as const

  return (
    <div className="space-y-4">
      <div>
        <p className="text-xs text-text-muted mb-2 font-medium">选择你感兴趣的主题</p>
        <div className="grid grid-cols-3 gap-2">
          {INTEREST_OPTIONS.map((opt) => (
            <button key={opt.key} onClick={() => toggle(opt.key)}
              className={`text-xs px-3 py-2 rounded-xl border transition-all ${
                prefs.interest.includes(opt.key)
                  ? 'bg-primary/20 border-primary/40 text-primary-light'
                  : 'bg-white/5 border-white/8 text-text-secondary hover:border-white/15'
              }`}>{opt.label}</button>
          ))}
        </div>
      </div>

      <div>
        <p className="text-xs text-text-muted mb-2 font-medium">体力强度：{STRENGTH_LABELS[prefs.physicalStrength]}</p>
        <div className="flex gap-2">
          {strengthKeys.map((k) => (
            <button key={k} onClick={() => setPrefs((p) => ({ ...p, physicalStrength: k }))}
              className={`flex-1 py-2 rounded-lg text-xs transition-all ${
                prefs.physicalStrength === k
                  ? 'bg-primary/20 border border-primary/40 text-primary-light'
                  : 'bg-white/5 border border-white/8 text-text-muted'
              }`}>{STRENGTH_LABELS[k]}</button>
          ))}
        </div>
      </div>

      <div>
        <p className="text-xs text-text-muted mb-2 font-medium">游览时长：{prefs.timeLimit} 分钟</p>
        <input type="range" min="30" max="240" step="15" value={prefs.timeLimit}
          onChange={(e) => setPrefs((p) => ({ ...p, timeLimit: Number(e.target.value) }))} className="w-full accent-primary" />
      </div>

      <div className="flex flex-wrap gap-2">
        {[
          { key: 'withChildren' as const, label: '👶 带小孩' },
          { key: 'withElderly' as const, label: '🧓 有老人' },
          { key: 'avoidCrowd' as const, label: '🚶 避开人流' },
        ].map((opt) => (
          <button key={opt.key} onClick={() => setPrefs((p) => ({ ...p, [opt.key]: !p[opt.key] }))}
            className={`text-xs px-3 py-1.5 rounded-lg border transition-all ${
              prefs[opt.key] ? 'bg-primary/15 border-primary/30 text-primary-light' : 'bg-white/5 border-white/8 text-text-muted'
            }`}>{opt.label}</button>
        ))}
      </div>

      <motion.button whileTap={{ scale: 0.96 }} onClick={recommend}
        disabled={loading || prefs.interest.length === 0}
        className="w-full py-3 rounded-xl bg-gradient-to-r from-primary to-accent text-white font-medium text-sm disabled:opacity-40 disabled:cursor-not-allowed">
        {loading ? '🧠 正在分析最佳路线...' : '✨ 智能推荐路线'}
      </motion.button>

      {result && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="glass rounded-2xl p-4 space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="font-semibold text-white">{result.routeName}</h4>
            <span className="text-xs text-accent">{result.estimatedTime}分钟</span>
          </div>
          <p className="text-xs text-text-secondary">{result.reason}</p>
          <div className="flex flex-wrap gap-1">
            {result.spots.map((s) => (
              <span key={s.spotId} className="text-[10px] px-2 py-0.5 rounded-lg bg-white/5 text-text-secondary">
                📍 {s.spotName} <span className="text-text-muted">{s.stayMinutes}min</span>
              </span>
            ))}
          </div>
          <div className="grid grid-cols-3 gap-2 text-center">
            <div className="glass rounded-lg py-2">
              <p className="text-sm font-bold text-accent">{result.distance}km</p>
              <p className="text-[10px] text-text-muted">距离</p>
            </div>
            <div className="glass rounded-lg py-2">
              <p className="text-sm font-bold text-warning">{result.difficulty || '-'}</p>
              <p className="text-[10px] text-text-muted">难度</p>
            </div>
            <div className="glass rounded-lg py-2">
              <p className="text-sm font-bold text-success">{result.matchedPreferences.length}</p>
              <p className="text-[10px] text-text-muted">偏好匹配</p>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  )
}
