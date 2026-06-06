import { useState } from 'react'
import { motion } from 'motion/react'
import StatCard from '../../components/admin/StatCard'
import TrendChart from '../../components/admin/TrendChart'

// Mock 数据
const SERVICE_DATA = [
  { name: '周一', 服务人次: 156, 满意数: 142, 语音问答: 89 },
  { name: '周二', 服务人次: 203, 满意数: 188, 语音问答: 134 },
  { name: '周三', 服务人次: 178, 满意数: 162, 语音问答: 102 },
  { name: '周四', 服务人次: 245, 满意数: 228, 语音问答: 167 },
  { name: '周五', 服务人次: 312, 满意数: 295, 语音问答: 221 },
  { name: '周六', 服务人次: 498, 满意数: 461, 语音问答: 356 },
  { name: '周日', 服务人次: 387, 满意数: 360, 语音问答: 278 },
]

const HOT_QUESTIONS = [
  { name: '大殿历史', count: 156 },
  { name: '钟楼故事', count: 132 },
  { name: '游览路线', count: 118 },
  { name: '建筑风格', count: 97 },
  { name: '拍照点位', count: 85 },
  { name: '开放时间', count: 72 },
  { name: '文物介绍', count: 68 },
  { name: '民俗文化', count: 54 },
]

const SATISFACTION_TREND = [
  { name: '第1周', 满意度: 87, 响应速度: 92 },
  { name: '第2周', 满意度: 89, 响应速度: 94 },
  { name: '第3周', 满意度: 91, 响应速度: 93 },
  { name: '第4周', 满意度: 93, 响应速度: 95 },
]

export default function AdminDashboard() {
  const [timeRange, setTimeRange] = useState<'day' | 'week' | 'month'>('week')

  return (
    <div className="h-full flex flex-col bg-[#0a0a1a]">
      {/* Header */}
      <div className="glass-strong px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-white">📊 数据大屏</h1>
          <p className="text-xs text-text-muted mt-0.5">景区AI导览运营总览</p>
        </div>
        <div className="flex gap-1 glass rounded-xl p-0.5">
          {[
            { key: 'day' as const, label: '今日' },
            { key: 'week' as const, label: '本周' },
            { key: 'month' as const, label: '本月' },
          ].map((r) => (
            <button
              key={r.key}
              onClick={() => setTimeRange(r.key)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                timeRange === r.key ? 'bg-accent/20 text-accent' : 'text-text-muted hover:text-text-secondary'
              }`}
            >
              {r.label}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {/* 核心指标 */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <StatCard icon="👥" label="今日服务人次" value="1,247" change="12%" changeType="up" color="primary" />
          <StatCard icon="💬" label="语音问答次数" value="856" change="8%" changeType="up" color="accent" />
          <StatCard icon="⭐" label="游客满意度" value="93.2%" change="2.1%" changeType="up" color="success" />
          <StatCard icon="⚡" label="平均响应延迟" value="2.3s" change="0.5s" changeType="down" color="warning" />
        </div>

        {/* 服务趋势图 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <TrendChart
            type="line"
            title="📈 本周服务趋势"
            data={SERVICE_DATA}
            dataKeys={[
              { key: '服务人次', color: '#6C5CE7', label: '服务人次' },
              { key: '语音问答', color: '#00D2FF', label: '语音问答' },
            ]}
          />
          <TrendChart
            type="bar"
            title="🔥 热门问答 TOP8"
            data={HOT_QUESTIONS}
            dataKeys={[{ key: 'count', color: '#00D2FF', label: '提问次数' }]}
            height={240}
          />
        </div>

        {/* 满意度趋势 + 实时信息 */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2">
            <TrendChart
              type="line"
              title="📊 满意度趋势（近4周）"
              data={SATISFACTION_TREND}
              dataKeys={[
                { key: '满意度', color: '#6C5CE7', label: '满意度(%)' },
                { key: '响应速度', color: '#51CF66', label: '响应速度(%)' },
              ]}
            />
          </div>

          {/* 实时状态卡片 */}
          <div className="glass rounded-2xl p-5 space-y-4">
            <h3 className="text-sm font-semibold text-white">🟢 实时状态</h3>
            <div className="space-y-3">
              {[
                { label: '在线数字人', value: 3, total: 3 },
                { label: '进行中导览团', value: 8, total: 12 },
                { label: '活跃游客数', value: 47, total: 89 },
                { label: '知识库条目', value: 128, total: 150 },
              ].map((item) => (
                <div key={item.label}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-text-secondary">{item.label}</span>
                    <span className="text-white font-medium">{item.value}/{item.total}</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-white/5 overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${(item.value / item.total) * 100}%` }}
                      transition={{ duration: 1, delay: 0.2 }}
                      className="h-full rounded-full bg-gradient-to-r from-primary to-accent"
                    />
                  </div>
                </div>
              ))}
            </div>

            <div className="glass rounded-xl p-3 text-center mt-4">
              <p className="text-xs text-text-muted">系统运行时间</p>
              <p className="text-sm font-mono text-accent mt-1">128 天 14 小时</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
