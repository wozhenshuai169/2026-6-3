import { motion } from 'motion/react'
import TrendChart from '../../components/admin/TrendChart'
import StatCard from '../../components/admin/StatCard'

const SENTIMENT_DATA = [
  { name: '第1周', 正向情感: 65, 中性: 20, 负向情感: 15 },
  { name: '第2周', 正向情感: 70, 中性: 18, 负向情感: 12 },
  { name: '第3周', 正向情感: 73, 中性: 17, 负向情感: 10 },
  { name: '第4周', 正向情感: 78, 中性: 14, 负向情感: 8 },
]

const TOPIC_CONCERN = [
  { name: '历史文化', 正面: 85, 中性: 10, 负面: 5 },
  { name: '路线规划', 正面: 70, 中性: 20, 负面: 10 },
  { name: '讲解质量', 正面: 82, 中性: 12, 负面: 6 },
  { name: '响应速度', 正面: 75, 中性: 15, 负面: 10 },
  { name: '语音体验', 正面: 68, 中性: 22, 负面: 10 },
]

const TOP_FEEDBACK = [
  { text: '数字人讲解很生动，孩子特别喜欢和它互动！', sentiment: 'positive', date: '2026-06-06' },
  { text: '希望能增加更多景点的AR实景讲解功能', sentiment: 'neutral', date: '2026-06-06' },
  { text: '语音识别在嘈杂环境下不够准确，需要改进', sentiment: 'negative', date: '2026-06-05' },
  { text: '路线推荐很合理，老人小孩都走得很轻松', sentiment: 'positive', date: '2026-06-05' },
  { text: '数字人回答很专业，比真人导游还详细', sentiment: 'positive', date: '2026-06-04' },
  { text: '拍照识别功能在光线暗的时候效果不太好', sentiment: 'negative', date: '2026-06-04' },
]

export default function AdminReports() {
  return (
    <div className="h-full flex flex-col bg-[#0a0a1a]">
      {/* Header */}
      <div className="glass-strong px-6 py-4">
        <h1 className="text-lg font-bold text-white">📋 游客感受度报告</h1>
        <p className="text-xs text-text-muted mt-0.5">情感趋势分析 · 游客反馈洞察</p>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {/* 指标卡片 */}
        <div className="grid grid-cols-3 gap-3">
          <StatCard icon="😊" label="正向情感占比" value="78%" change="13%" changeType="up" color="success" />
          <StatCard icon="😐" label="中性情感占比" value="14%" change="6%" changeType="down" color="warning" />
          <StatCard icon="😟" label="负向情感占比" value="8%" change="7%" changeType="down" color="danger" />
        </div>

        {/* 情感趋势 */}
        <TrendChart
          type="line"
          title="📈 四周情感趋势变化"
          data={SENTIMENT_DATA}
          dataKeys={[
            { key: '正向情感', color: '#51CF66', label: '正向' },
            { key: '中性', color: '#FFD43B', label: '中性' },
            { key: '负向情感', color: '#FF6B6B', label: '负向' },
          ]}
        />

        {/* 话题关注度 */}
        <div className="glass rounded-2xl p-5">
          <h3 className="text-sm font-semibold text-white mb-4">💡 话题关注度与情感分布</h3>
          <div className="space-y-3">
            {TOPIC_CONCERN.map((topic) => (
              <div key={topic.name}>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs text-text-secondary">{topic.name}</span>
                  <div className="flex gap-2 text-[10px]">
                    <span className="text-success">{topic.正面}% 正面</span>
                    <span className="text-warning">{topic.中性}%</span>
                    <span className="text-danger">{topic.负面}% 负面</span>
                  </div>
                </div>
                <div className="h-2 rounded-full bg-white/5 overflow-hidden flex">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${topic.正面}%` }}
                    transition={{ duration: 0.8 }}
                    className="h-full bg-success/60"
                  />
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${topic.中性}%` }}
                    transition={{ duration: 0.8, delay: 0.2 }}
                    className="h-full bg-warning/60"
                  />
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${topic.负面}%` }}
                    transition={{ duration: 0.8, delay: 0.4 }}
                    className="h-full bg-danger/60"
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 游客反馈列表 */}
        <div className="glass rounded-2xl p-5">
          <h3 className="text-sm font-semibold text-white mb-4">💬 近期游客反馈</h3>
          <div className="space-y-2">
            {TOP_FEEDBACK.map((fb, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.1 }}
                className="flex items-start gap-3 bg-white/5 rounded-xl p-3"
              >
                <span className="text-lg flex-shrink-0">
                  {fb.sentiment === 'positive' ? '😊' : fb.sentiment === 'negative' ? '😟' : '😐'}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-text-secondary leading-relaxed">{fb.text}</p>
                  <p className="text-[10px] text-text-muted mt-1">{fb.date}</p>
                </div>
                <span className={`text-[10px] px-2 py-0.5 rounded-full flex-shrink-0 ${
                  fb.sentiment === 'positive' ? 'bg-success/15 text-success' :
                  fb.sentiment === 'negative' ? 'bg-danger/15 text-danger' :
                  'bg-warning/15 text-warning'
                }`}>
                  {fb.sentiment === 'positive' ? '正向' : fb.sentiment === 'negative' ? '负向' : '中性'}
                </span>
              </motion.div>
            ))}
          </div>
        </div>

        {/* 改进建议 */}
        <div className="glass rounded-2xl p-5 bg-gradient-to-br from-primary/10 to-accent/5 border border-primary/15">
          <h3 className="text-sm font-semibold text-white mb-3">💡 AI 改进建议</h3>
          <div className="space-y-2">
            {[
              '游客对数字人的历史讲解满意度持续上升，建议保持现有讲解深度',
              '约10%游客反映语音识别在嘈杂环境需改进，建议优化降噪方案',
              '拍照识别功能的准确度受到光线条件影响，建议增加图像增强预处理',
              '游客对AR实景功能有较高期待，建议纳入下一阶段产品规划',
            ].map((rec, i) => (
              <div key={i} className="flex items-start gap-2 text-xs text-text-secondary">
                <span className="text-accent mt-0.5">✦</span>
                <p>{rec}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
