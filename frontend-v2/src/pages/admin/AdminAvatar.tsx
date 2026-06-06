import { useState } from 'react'
import { motion } from 'motion/react'

interface AvatarConfig {
  appearance: string
  clothing: string
  voice: string
  speakingSpeed: number
  emotionStyle: string
  greeting: string
}

const INITIAL_CONFIG: AvatarConfig = {
  appearance: 'classic',
  clothing: 'hanfu',
  voice: 'gentle_female',
  speakingSpeed: 1.0,
  emotionStyle: 'friendly',
  greeting: '欢迎来到灵境古苑！我是您的AI数字人导游小灵，很高兴为您服务。',
}

const APPEARANCES = [
  { id: 'classic', name: '经典形象', icon: '👩‍🦰', desc: '优雅知性，适配古建景区' },
  { id: 'modern', name: '现代简约', icon: '👩‍💼', desc: '清爽干练，专业导游风' },
  { id: 'cute', name: '可爱活泼', icon: '👧', desc: '亲切阳光，亲子游首选' },
]

const CLOTHING_OPTIONS = [
  { id: 'hanfu', name: '汉服', icon: '👘' },
  { id: 'qipao', name: '旗袍', icon: '🥻' },
  { id: 'uniform', name: '导游制服', icon: '👔' },
  { id: 'casual', name: '休闲装', icon: '👕' },
]

const VOICE_OPTIONS = [
  { id: 'gentle_female', name: '温柔女声', desc: '清甜柔和，适合讲解' },
  { id: 'professional_female', name: '专业女声', desc: '清晰标准，适合正式场合' },
  { id: 'warm_male', name: '温暖男声', desc: '浑厚稳重，适合历史讲解' },
  { id: 'lively_male', name: '活泼男声', desc: '生动有趣，适合互动问答' },
]

export default function AdminAvatar() {
  const [config, setConfig] = useState<AvatarConfig>(INITIAL_CONFIG)
  const [saved, setSaved] = useState(false)

  const updateConfig = <K extends keyof AvatarConfig>(key: K, value: AvatarConfig[K]) => {
    setConfig((c) => ({ ...c, [key]: value }))
    setSaved(false)
  }

  const handleSave = () => {
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  return (
    <div className="h-full flex flex-col bg-[#0a0a1a]">
      {/* Header */}
      <div className="glass-strong px-6 py-4">
        <h1 className="text-lg font-bold text-white">🎭 数字人形象管理</h1>
        <p className="text-xs text-text-muted mt-0.5">配置数字人导游的外观、服装和声音</p>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-5">
        {/* 预览区 */}
        <div className="glass rounded-2xl p-6 flex flex-col items-center">
          <div className="w-24 h-24 rounded-full flex items-center justify-center text-5xl mb-4"
            style={{ background: 'radial-gradient(circle at 40% 35%, rgba(108,92,231,0.3), rgba(0,210,255,0.1))' }}>
            {APPEARANCES.find((a) => a.id === config.appearance)?.icon || '🤖'}
          </div>
          <p className="text-sm font-semibold text-white">
            {APPEARANCES.find((a) => a.id === config.appearance)?.name || '数字人'}
          </p>
          <p className="text-[10px] text-text-muted mt-0.5">
            {CLOTHING_OPTIONS.find((c) => c.id === config.clothing)?.icon}
            {' '}
            {CLOTHING_OPTIONS.find((c) => c.id === config.clothing)?.name}
            {' · '}
            {VOICE_OPTIONS.find((v) => v.id === config.voice)?.name}
          </p>
        </div>

        {/* 外观选择 */}
        <div className="glass rounded-2xl p-5">
          <h2 className="text-sm font-semibold text-white mb-3">👤 外观形象</h2>
          <div className="grid grid-cols-3 gap-3">
            {APPEARANCES.map((a) => (
              <button
                key={a.id}
                onClick={() => updateConfig('appearance', a.id)}
                className={`p-3 rounded-xl text-center transition-all ${
                  config.appearance === a.id
                    ? 'bg-primary/20 border border-primary/40'
                    : 'bg-white/5 border border-white/8 hover:border-white/15'
                }`}
              >
                <span className="text-2xl block mb-1">{a.icon}</span>
                <p className="text-xs text-white font-medium">{a.name}</p>
                <p className="text-[10px] text-text-muted mt-0.5">{a.desc}</p>
              </button>
            ))}
          </div>
        </div>

        {/* 服装选择 */}
        <div className="glass rounded-2xl p-5">
          <h2 className="text-sm font-semibold text-white mb-3">👘 服装风格</h2>
          <div className="grid grid-cols-4 gap-2">
            {CLOTHING_OPTIONS.map((c) => (
              <button
                key={c.id}
                onClick={() => updateConfig('clothing', c.id)}
                className={`p-3 rounded-xl text-center transition-all ${
                  config.clothing === c.id
                    ? 'bg-accent/20 border border-accent/40'
                    : 'bg-white/5 border border-white/8 hover:border-white/15'
                }`}
              >
                <span className="text-xl block">{c.icon}</span>
                <p className="text-[10px] text-white mt-1">{c.name}</p>
              </button>
            ))}
          </div>
        </div>

        {/* 声音选择 */}
        <div className="glass rounded-2xl p-5">
          <h2 className="text-sm font-semibold text-white mb-3">🔊 声音配置</h2>
          <div className="space-y-2">
            {VOICE_OPTIONS.map((v) => (
              <button
                key={v.id}
                onClick={() => updateConfig('voice', v.id)}
                className={`w-full p-3 rounded-xl text-left flex items-center gap-3 transition-all ${
                  config.voice === v.id
                    ? 'bg-primary/20 border border-primary/40'
                    : 'bg-white/5 border border-white/8 hover:border-white/15'
                }`}
              >
                <div className={`w-3 h-3 rounded-full border-2 flex items-center justify-center ${
                  config.voice === v.id ? 'border-primary' : 'border-white/20'
                }`}>
                  {config.voice === v.id && <div className="w-1.5 h-1.5 rounded-full bg-primary" />}
                </div>
                <div>
                  <p className="text-sm text-white">{v.name}</p>
                  <p className="text-[10px] text-text-muted">{v.desc}</p>
                </div>
                {config.voice === v.id && (
                  <span className="ml-auto text-sm">🔊</span>
                )}
              </button>
            ))}
          </div>

          {/* 语速 */}
          <div className="mt-4 pt-4 border-t border-white/5">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-text-secondary">语速</span>
              <span className="text-xs text-accent">{config.speakingSpeed.toFixed(1)}x</span>
            </div>
            <input
              type="range" min="0.5" max="2.0" step="0.1"
              value={config.speakingSpeed}
              onChange={(e) => updateConfig('speakingSpeed', Number(e.target.value))}
              className="w-full accent-primary"
            />
            <div className="flex justify-between text-[10px] text-text-muted mt-1">
              <span>慢</span><span>正常</span><span>快</span>
            </div>
          </div>
        </div>

        {/* 情感风格 */}
        <div className="glass rounded-2xl p-5">
          <h2 className="text-sm font-semibold text-white mb-3">😊 情感风格</h2>
          <div className="grid grid-cols-3 gap-2">
            {[
              { id: 'friendly', label: '亲切友好', icon: '😊' },
              { id: 'professional', label: '专业严谨', icon: '🤓' },
              { id: 'enthusiastic', label: '热情洋溢', icon: '🤗' },
            ].map((e) => (
              <button
                key={e.id}
                onClick={() => updateConfig('emotionStyle', e.id)}
                className={`p-3 rounded-xl text-center transition-all ${
                  config.emotionStyle === e.id
                    ? 'bg-success/20 border border-success/40'
                    : 'bg-white/5 border border-white/8 hover:border-white/15'
                }`}
              >
                <span className="text-xl block">{e.icon}</span>
                <p className="text-[10px] text-white mt-1">{e.label}</p>
              </button>
            ))}
          </div>
        </div>

        {/* 欢迎语 */}
        <div className="glass rounded-2xl p-5">
          <h2 className="text-sm font-semibold text-white mb-3">💬 欢迎语</h2>
          <textarea
            value={config.greeting}
            onChange={(e) => updateConfig('greeting', e.target.value)}
            rows={3}
            className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder:text-text-muted focus:outline-none focus:border-primary/50 resize-none"
          />
        </div>

        {/* 保存 */}
        <motion.button
          whileTap={{ scale: 0.97 }}
          onClick={handleSave}
          className={`w-full py-3.5 rounded-xl font-semibold text-sm transition-all ${
            saved
              ? 'bg-success/20 border border-success/40 text-success'
              : 'bg-gradient-to-r from-primary to-accent text-white'
          }`}
        >
          {saved ? '✅ 配置已保存' : '💾 保存配置'}
        </motion.button>
      </div>
    </div>
  )
}
