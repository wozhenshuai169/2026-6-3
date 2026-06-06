import { useState } from 'react'
import { motion } from 'motion/react'

interface KnowledgeItem {
  id: string
  title: string
  category: string
  content: string
  tags: string[]
  updatedAt: string
}

interface KnowledgeEditorProps {
  item: KnowledgeItem | null
  onSave: (item: KnowledgeItem) => void
  onCancel: () => void
}

const CATEGORIES = ['景点介绍', '历史典故', '建筑艺术', '民俗文化', '自然生态', 'FAQ']

export default function KnowledgeEditor({ item, onSave, onCancel }: KnowledgeEditorProps) {
  const [title, setTitle] = useState(item?.title || '')
  const [category, setCategory] = useState(item?.category || CATEGORIES[0])
  const [content, setContent] = useState(item?.content || '')
  const [tagInput, setTagInput] = useState('')
  const [tags, setTags] = useState<string[]>(item?.tags || [])

  const addTag = () => {
    const t = tagInput.trim()
    if (t && !tags.includes(t)) setTags([...tags, t])
    setTagInput('')
  }

  const removeTag = (t: string) => setTags(tags.filter((x) => x !== t))

  const handleSave = () => {
    onSave({
      id: item?.id || `kb_${Date.now()}`,
      title: title.trim(),
      category,
      content: content.trim(),
      tags,
      updatedAt: new Date().toISOString(),
    })
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass rounded-2xl p-5 space-y-4"
    >
      <h3 className="text-sm font-semibold text-white">
        {item ? '编辑知识条目' : '新增知识条目'}
      </h3>

      <div>
        <label className="text-xs text-text-muted mb-1.5 block">标题</label>
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="知识条目标题..."
          className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-text-muted focus:outline-none focus:border-primary/50"
        />
      </div>

      <div>
        <label className="text-xs text-text-muted mb-1.5 block">分类</label>
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-primary/50"
        >
          {CATEGORIES.map((c) => (
            <option key={c} value={c} className="bg-[#1a1a2e]">{c}</option>
          ))}
        </select>
      </div>

      <div>
        <label className="text-xs text-text-muted mb-1.5 block">内容</label>
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="知识内容..."
          rows={8}
          className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder:text-text-muted focus:outline-none focus:border-primary/50 resize-none"
        />
      </div>

      <div>
        <label className="text-xs text-text-muted mb-1.5 block">标签</label>
        <div className="flex gap-2 mb-2 flex-wrap">
          {tags.map((t) => (
            <span key={t} className="inline-flex items-center gap-1 text-[10px] px-2 py-1 rounded-lg bg-primary/15 text-primary-light">
              {t}
              <button onClick={() => removeTag(t)} className="hover:text-danger">×</button>
            </span>
          ))}
        </div>
        <div className="flex gap-2">
          <input
            value={tagInput}
            onChange={(e) => setTagInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && addTag()}
            placeholder="添加标签..."
            className="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-white placeholder:text-text-muted focus:outline-none focus:border-primary/50"
          />
          <button onClick={addTag} className="px-3 py-2 rounded-lg bg-white/5 text-xs text-text-secondary hover:text-accent transition-colors">
            + 添加
          </button>
        </div>
      </div>

      <div className="flex gap-3 pt-2">
        <button onClick={onCancel} className="flex-1 py-2.5 rounded-xl bg-white/5 border border-white/10 text-text-secondary text-sm">
          取消
        </button>
        <button
          onClick={handleSave}
          disabled={!title.trim() || !content.trim()}
          className="flex-1 py-2.5 rounded-xl bg-gradient-to-r from-primary to-accent text-white text-sm font-medium disabled:opacity-40"
        >
          保存
        </button>
      </div>
    </motion.div>
  )
}
