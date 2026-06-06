import { motion, type PanInfo } from 'motion/react'
import type { ReactNode } from 'react'

interface GlassPanelProps {
  open: boolean
  onClose: () => void
  children: ReactNode
  title?: string
  height?: string // e.g. '60vh'
}

export default function GlassPanel({ open, onClose, children, title, height = '55vh' }: GlassPanelProps) {
  const handleDrag = (_: unknown, info: PanInfo) => {
    if (info.offset.y > 100) onClose()
  }

  return (
    <motion.div
      initial={{ y: '100%' }}
      animate={{ y: open ? '0%' : '95%' }}
      exit={{ y: '100%' }}
      transition={{ type: 'spring', damping: 25, stiffness: 200 }}
      drag="y"
      dragConstraints={{ top: 0, bottom: 0 }}
      dragElastic={0.1}
      onDragEnd={handleDrag}
      className="glass-strong absolute bottom-0 left-0 right-0 rounded-t-2xl z-40 overflow-hidden"
      style={{ height }}
    >
      {/* 拖拽手柄 */}
      <div className="flex justify-center pt-2 pb-1 cursor-grab active:cursor-grabbing">
        <div className="w-10 h-1 rounded-full bg-white/20" />
      </div>

      {title && (
        <div className="px-5 pb-2 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-text-secondary">{title}</h3>
          <button onClick={onClose} className="text-text-muted hover:text-text-primary text-lg leading-none">
            ✕
          </button>
        </div>
      )}

      <div className="overflow-y-auto px-4 pb-6" style={{ height: 'calc(100% - 36px)' }}>
        {children}
      </div>
    </motion.div>
  )
}
