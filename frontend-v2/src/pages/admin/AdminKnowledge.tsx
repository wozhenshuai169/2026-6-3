import { useState } from 'react'
import { motion, AnimatePresence } from 'motion/react'
import KnowledgeEditor from '../../components/admin/KnowledgeEditor'

interface KnowledgeItem {
  id: string
  title: string
  category: string
  content: string
  tags: string[]
  updatedAt: string
}

const MOCK_ITEMS: KnowledgeItem[] = [
  {
    id: '1', title: '大殿建筑特色', category: '建筑艺术',
    content: '大殿建于清代乾隆年间（公元1751年），面阔五间，进深三间，重檐歇山顶。殿内保存有大量清代彩绘和木雕，斗拱结构精巧，是典型的清代官式建筑代表。',
    tags: ['大殿', '建筑', '清代'], updatedAt: '2026-06-05T14:30:00Z'
  },
  {
    id: '2', title: '钟楼铜钟历史', category: '历史典故',
    content: '钟楼内悬挂的铜钟铸造于明万历四十二年（公元1614年），钟身高2.8米，直径1.9米，重达三吨。钟身铸有铭文和精美纹饰，钟声浑厚悠远，可传十里之外。',
    tags: ['钟楼', '明代', '文物'], updatedAt: '2026-06-04T10:00:00Z'
  },
  {
    id: '3', title: '石雕长廊艺术价值', category: '建筑艺术',
    content: '石雕长廊全长120米，汇集了唐、宋、元、明、清历代石雕精品。长廊内共有浮雕108幅，圆雕36尊，题材涵盖神话传说、历史故事、花鸟鱼虫等。',
    tags: ['石雕', '长廊', '艺术'], updatedAt: '2026-06-03T16:00:00Z'
  },
  {
    id: '4', title: '游览路线推荐FAQ', category: 'FAQ',
    content: 'Q: 景区有哪些推荐游览路线？A: 经典文化之旅（约90分钟）、深度探索之旅（约150分钟）、轻松休闲之旅（约60分钟）。您可根据自己的兴趣和体力选择合适的路线。',
    tags: ['FAQ', '路线', '推荐'], updatedAt: '2026-06-02T09:00:00Z'
  },
  {
    id: '5', title: '中庭古树群', category: '自然生态',
    content: '中庭区域生长着十余棵百年以上的古树，包括银杏、国槐、侧柏等。其中树龄最大的一棵银杏已有320年历史，树高25米，冠幅达18米，是国家一级保护古树。',
    tags: ['中庭', '古树', '自然'], updatedAt: '2026-06-01T11:00:00Z'
  },
]

export default function AdminKnowledge() {
  const [items, setItems] = useState<KnowledgeItem[]>(MOCK_ITEMS)
  const [editing, setEditing] = useState<KnowledgeItem | null>(null)
  const [creating, setCreating] = useState(false)
  const [search, setSearch] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('全部')

  const categories = ['全部', ...new Set(items.map((i) => i.category))]

  const filtered = items.filter((i) => {
    const matchSearch = !search || i.title.includes(search) || i.content.includes(search) || i.tags.some((t) => t.includes(search))
    const matchCat = categoryFilter === '全部' || i.category === categoryFilter
    return matchSearch && matchCat
  })

  const handleSave = (item: KnowledgeItem) => {
    setItems((prev) => {
      const idx = prev.findIndex((i) => i.id === item.id)
      if (idx >= 0) {
        const next = [...prev]
        next[idx] = item
        return next
      }
      return [item, ...prev]
    })
    setEditing(null)
    setCreating(false)
  }

  const handleDelete = (id: string) => {
    setItems((prev) => prev.filter((i) => i.id !== id))
  }

  return (
    <div className="h-full flex flex-col bg-[#0a0a1a]">
      {/* Header */}
      <div className="glass-strong px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-white">📚 知识库管理</h1>
          <p className="text-xs text-text-muted mt-0.5">{items.length}条知识条目</p>
        </div>
        <button
          onClick={() => setCreating(true)}
          className="px-4 py-2 rounded-xl bg-gradient-to-r from-primary to-accent text-white text-sm font-medium"
        >
          + 新增条目
        </button>
      </div>

      {/* 搜索和筛选 */}
      <div className="px-4 py-3 flex gap-3">
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="搜索知识条目..."
          className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-text-muted focus:outline-none focus:border-primary/50"
        />
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-sm text-white focus:outline-none"
        >
          {categories.map((c) => (
            <option key={c} value={c} className="bg-[#1a1a2e]">{c}</option>
          ))}
        </select>
      </div>

      {/* 内容区 */}
      <div className="flex-1 overflow-y-auto px-4 pb-4">
        <AnimatePresence mode="wait">
          {(editing || creating) ? (
            <KnowledgeEditor
              key={editing?.id || 'new'}
              item={editing}
              onSave={handleSave}
              onCancel={() => { setEditing(null); setCreating(false) }}
            />
          ) : (
            <div className="space-y-2">
              {filtered.length === 0 ? (
                <div className="text-center py-12 text-text-muted">
                  <span className="text-4xl">📭</span>
                  <p className="text-sm mt-3">未找到匹配的知识条目</p>
                </div>
              ) : (
                filtered.map((item) => (
                  <motion.div
                    key={item.id}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="glass rounded-xl p-4"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-[10px] px-2 py-0.5 rounded-lg bg-accent/10 text-accent">
                            {item.category}
                          </span>
                          <h3 className="text-sm font-semibold text-white truncate">{item.title}</h3>
                        </div>
                        <p className="text-xs text-text-secondary line-clamp-2 leading-relaxed">
                          {item.content}
                        </p>
                        <div className="flex items-center gap-2 mt-2">
                          {item.tags.map((t) => (
                            <span key={t} className="text-[10px] text-text-muted">#{t}</span>
                          ))}
                          <span className="text-[10px] text-text-muted ml-auto">
                            {new Date(item.updatedAt).toLocaleDateString('zh-CN')}
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-1 ml-3">
                        <button
                          onClick={() => setEditing(item)}
                          className="p-2 rounded-lg hover:bg-white/10 text-text-muted hover:text-accent transition-all text-xs"
                        >
                          ✏️
                        </button>
                        <button
                          onClick={() => handleDelete(item.id)}
                          className="p-2 rounded-lg hover:bg-white/10 text-text-muted hover:text-danger transition-all text-xs"
                        >
                          🗑️
                        </button>
                      </div>
                    </div>
                  </motion.div>
                ))
              )}
            </div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}
