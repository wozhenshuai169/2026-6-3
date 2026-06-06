import { motion } from 'motion/react'

export function PageLoader({ text = '加载中...' }: { text?: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-6">
      <div className="relative w-16 h-16">
        <motion.div
          className="absolute inset-0 rounded-full border-2 border-transparent border-t-accent"
          animate={{ rotate: 360 }}
          transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}
        />
        <motion.div
          className="absolute inset-2 rounded-full border-2 border-transparent border-t-primary-light"
          animate={{ rotate: -360 }}
          transition={{ repeat: Infinity, duration: 1.5, ease: 'linear' }}
        />
      </div>
      <p className="text-text-secondary text-sm animate-pulse">{text}</p>
    </div>
  )
}

export function Skeleton({ className = '' }: { className?: string }) {
  return (
    <div className={`animate-pulse rounded-xl bg-white/5 ${className}`} />
  )
}
