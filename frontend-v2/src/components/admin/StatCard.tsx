import { motion } from 'motion/react'

interface StatCardProps {
  icon: string
  label: string
  value: string | number
  change?: string
  changeType?: 'up' | 'down' | 'neutral'
  color?: 'primary' | 'accent' | 'success' | 'warning' | 'danger'
}

const colorMap = {
  primary: { bg: 'from-primary/20 to-primary/5', border: 'border-primary/20', text: 'text-primary-light' },
  accent: { bg: 'from-accent/20 to-accent/5', border: 'border-accent/20', text: 'text-accent' },
  success: { bg: 'from-success/20 to-success/5', border: 'border-success/20', text: 'text-success' },
  warning: { bg: 'from-warning/20 to-warning/5', border: 'border-warning/20', text: 'text-warning' },
  danger: { bg: 'from-danger/20 to-danger/5', border: 'border-danger/20', text: 'text-danger' },
}

export default function StatCard({ icon, label, value, change, changeType = 'neutral', color = 'primary' }: StatCardProps) {
  const c = colorMap[color]
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className={`glass rounded-2xl p-5 bg-gradient-to-br ${c.bg} border ${c.border}`}
    >
      <div className="flex items-center justify-between mb-3">
        <span className="text-2xl">{icon}</span>
        {change && (
          <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
            changeType === 'up' ? 'bg-success/15 text-success' :
            changeType === 'down' ? 'bg-danger/15 text-danger' :
            'bg-white/10 text-text-muted'
          }`}>
            {changeType === 'up' ? '↑' : changeType === 'down' ? '↓' : ''} {change}
          </span>
        )}
      </div>
      <p className={`text-2xl font-bold ${c.text}`}>{value}</p>
      <p className="text-xs text-text-muted mt-1">{label}</p>
    </motion.div>
  )
}
