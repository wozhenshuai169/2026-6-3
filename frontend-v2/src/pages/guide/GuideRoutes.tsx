import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'motion/react'

interface Route {
  id: string
  name: string
  spots: string[]
  estimatedTime: number
  distance: number
  difficulty: number
  tags: string[]
  description: string
}

const MOCK_ROUTES: Route[] = [
  {
    id: 'route_1',
    name: '经典文化之旅',
    spots: ['大殿', '钟楼', '鼓楼', '中庭'],
    estimatedTime: 90,
    distance: 1.8,
    difficulty: 2,
    tags: ['历史文化', '建筑'],
    description: '领略灵境古苑核心建筑群，感受清代建筑的精湛工艺和深厚的文化底蕴。适合首次到访的游客。',
  },
  {
    id: 'route_2',
    name: '深度探索之旅',
    spots: ['大殿', '石雕长廊', '钟楼', '中庭', '东门'],
    estimatedTime: 150,
    distance: 3.2,
    difficulty: 3,
    tags: ['深度游', '艺术', '摄影'],
    description: '全面覆盖园区主要景点，包含石雕长廊的详细讲解和多个拍照打卡点。适合文化爱好者和摄影爱好者。',
  },
  {
    id: 'route_3',
    name: '轻松休闲之旅',
    spots: ['服务中心', '中庭', '大殿'],
    estimatedTime: 60,
    distance: 1.2,
    difficulty: 1,
    tags: ['轻松', '亲子', '老年'],
    description: '精选核心景点，路程平坦轻松。适合带老人小孩的家庭出游，节奏舒缓，休息点多。',
  },
  {
    id: 'route_4',
    name: '古建寻踪之旅',
    spots: ['东门', '鼓楼', '大殿', '石雕长廊'],
    estimatedTime: 120,
    distance: 2.5,
    difficulty: 3,
    tags: ['建筑', '历史', '研究'],
    description: '聚焦园区的建筑艺术价值，从明代东门到清代大殿，再到历代石雕，是一部立体的中国建筑史。',
  },
]

export default function GuideRoutes() {
  const navigate = useNavigate()
  const [selectedRoute, setSelectedRoute] = useState<string | null>(null)

  const route = MOCK_ROUTES.find((r) => r.id === selectedRoute)

  return (
    <div className="h-full flex flex-col bg-[#0a0a1a]">
      {/* Header */}
      <div className="glass-strong px-4 py-3 flex items-center gap-3">
        <button onClick={() => navigate('/guide')} className="text-text-secondary hover:text-white text-lg">←</button>
        <div>
          <h1 className="text-sm font-bold text-white">🗺️ 路线管理</h1>
          <p className="text-[10px] text-text-muted">{MOCK_ROUTES.length}条预设路线</p>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* 路线列表 */}
        <div className={`${selectedRoute ? 'hidden md:flex' : 'flex'} flex-col w-full md:w-80 flex-shrink-0 overflow-y-auto px-3 py-3 space-y-2 border-r border-white/5`}>
          {MOCK_ROUTES.map((r) => (
            <motion.div
              key={r.id}
              whileTap={{ scale: 0.98 }}
              onClick={() => setSelectedRoute(r.id)}
              className={`glass rounded-xl p-4 cursor-pointer transition-all ${
                selectedRoute === r.id ? 'border-accent/40' : 'hover:border-white/15'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-semibold text-white">{r.name}</h3>
                  <p className="text-xs text-text-secondary mt-1 line-clamp-2">{r.description}</p>
                </div>
              </div>
              <div className="flex items-center gap-2 mt-2 flex-wrap">
                <span className="text-[10px] px-2 py-0.5 rounded-lg bg-white/5 text-text-muted">⏱ {r.estimatedTime}min</span>
                <span className="text-[10px] px-2 py-0.5 rounded-lg bg-white/5 text-text-muted">📏 {r.distance}km</span>
                <span className="text-[10px] px-2 py-0.5 rounded-lg bg-white/5 text-text-muted">{'⭐'.repeat(r.difficulty)}</span>
              </div>
              <div className="flex gap-1 mt-2 flex-wrap">
                {r.tags.map((t) => (
                  <span key={t} className="text-[9px] px-1.5 py-0.5 rounded-md bg-accent/10 text-accent">{t}</span>
                ))}
              </div>
            </motion.div>
          ))}
        </div>

        {/* 路线详情 */}
        <div className={`${selectedRoute ? 'flex' : 'hidden md:flex'} flex-col flex-1 overflow-y-auto px-4 py-4`}>
          {route ? (
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="space-y-4"
            >
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-bold text-white">{route.name}</h2>
                <button onClick={() => setSelectedRoute(null)} className="md:hidden text-text-muted hover:text-white">
                  ✕
                </button>
              </div>

              <p className="text-sm text-text-secondary leading-relaxed">{route.description}</p>

              <div className="grid grid-cols-3 gap-3">
                <div className="glass rounded-xl p-3 text-center">
                  <p className="text-xl font-bold text-accent">{route.estimatedTime}</p>
                  <p className="text-[10px] text-text-muted">分钟</p>
                </div>
                <div className="glass rounded-xl p-3 text-center">
                  <p className="text-xl font-bold text-primary-light">{route.distance}</p>
                  <p className="text-[10px] text-text-muted">公里</p>
                </div>
                <div className="glass rounded-xl p-3 text-center">
                  <p className="text-xl font-bold text-warning">{'⭐'.repeat(route.difficulty)}</p>
                  <p className="text-[10px] text-text-muted">难度</p>
                </div>
              </div>

              <div>
                <h3 className="text-sm font-semibold text-white mb-2">🗺️ 路线节点</h3>
                <div className="space-y-2">
                  {route.spots.map((spot, i) => (
                    <div key={spot} className="flex items-center gap-3 glass rounded-xl px-4 py-3">
                      <div className="w-6 h-6 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center text-xs font-bold text-white">
                        {i + 1}
                      </div>
                      <span className="text-sm text-white">{spot}</span>
                      {i < route.spots.length - 1 && (
                        <span className="text-text-muted text-xs ml-auto">→ {Math.round(route.distance / (route.spots.length - 1) * 10) / 10}km</span>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => navigate(-1)}
                  className="flex-1 py-3 rounded-xl bg-white/5 border border-white/10 text-text-secondary text-sm font-medium"
                >
                  返回
                </button>
                <button
                  onClick={() => navigate(-1)}
                  className="flex-1 py-3 rounded-xl bg-gradient-to-r from-primary to-accent text-white text-sm font-medium"
                >
                  ✅ 选用此路线
                </button>
              </div>
            </motion.div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-text-muted gap-3">
              <span className="text-5xl">🗺️</span>
              <p className="text-sm">选择一条路线查看详情</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
