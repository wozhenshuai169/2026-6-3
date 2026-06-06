import { motion } from 'motion/react'
import { useRoomStore } from '../../stores/roomStore'

// 模拟景区景点坐标
const SPOTS: { id: string; name: string; x: number; y: number; icon: string }[] = [
  { id: 'main_hall', name: '大殿', x: 50, y: 35, icon: '🏛️' },
  { id: 'bell_tower', name: '钟楼', x: 22, y: 28, icon: '🔔' },
  { id: 'drum_tower', name: '鼓楼', x: 75, y: 30, icon: '🥁' },
  { id: 'courtyard', name: '中庭', x: 48, y: 55, icon: '🌳' },
  { id: 'gallery', name: '石雕长廊', x: 28, y: 68, icon: '🗿' },
  { id: 'service', name: '服务中心', x: 85, y: 62, icon: '🏪' },
  { id: 'east_gate', name: '东门', x: 55, y: 82, icon: '⛩️' },
]

export default function ScenicMap() {
  const currentSpot = useRoomStore((s) => s.currentSpot)

  return (
    <div className="relative w-full aspect-[4/3] rounded-2xl overflow-hidden bg-white/3 border border-white/5">
      {/* 地图底纹 */}
      <div className="absolute inset-0 opacity-10"
        style={{
          backgroundImage: 'radial-gradient(circle, rgba(108,92,231,0.3) 1px, transparent 1px)',
          backgroundSize: '20px 20px',
        }}
      />

      {/* 路径线（简化为直线连接） */}
      <svg className="absolute inset-0 w-full h-full" viewBox="0 0 100 100">
        <path
          d="M50,35 L22,28 L48,55 L28,68 M50,35 L75,30 L85,62 L55,82 M48,55 L55,82"
          fill="none"
          stroke="rgba(255,255,255,0.12)"
          strokeWidth="0.5"
          strokeDasharray="2,2"
        />
      </svg>

      {/* 景点标记 */}
      {SPOTS.map((spot) => {
        const isCurrent = spot.id === currentSpot
        return (
          <motion.div
            key={spot.id}
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: Math.random() * 0.3 }}
            className={`absolute -translate-x-1/2 -translate-y-1/2 flex flex-col items-center gap-0.5 cursor-pointer ${
              isCurrent ? 'z-10' : 'z-0'
            }`}
            style={{ left: `${spot.x}%`, top: `${spot.y}%` }}
          >
            <motion.span
              animate={isCurrent ? { scale: [1, 1.2, 1] } : {}}
              transition={{ repeat: Infinity, duration: 1.5 }}
              className={`text-xl ${isCurrent ? 'text-2xl drop-shadow-[0_0_8px_rgba(0,210,255,0.6)]' : 'opacity-60'}`}
            >
              {spot.icon}
            </motion.span>
            <span className={`text-[9px] whitespace-nowrap ${
              isCurrent ? 'text-accent font-medium' : 'text-text-muted'
            }`}>
              {spot.name}
            </span>
            {isCurrent && (
              <motion.div
                className="absolute inset-0 rounded-full border border-accent/50"
                animate={{ scale: [1, 1.5], opacity: [0.5, 0] }}
                transition={{ repeat: Infinity, duration: 2 }}
                style={{ width: 32, height: 32, top: -6, left: -2 }}
              />
            )}
          </motion.div>
        )
      })}

      {/* 图例 */}
      <div className="absolute bottom-2 right-2 glass rounded-lg px-2 py-1 text-[10px] text-text-muted">
        灵境古苑 · 导览地图
      </div>
    </div>
  )
}
