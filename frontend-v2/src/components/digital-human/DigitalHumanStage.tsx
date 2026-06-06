import { Suspense, useState, useEffect, Component } from 'react'
import { Canvas } from '@react-three/fiber'
import { Environment } from '@react-three/drei'
import AvatarHead from './AvatarHead'
import AvatarParticles from './AvatarParticles'
import AvatarHalo from './AvatarHalo'
import AvatarFallback from './AvatarFallback'
import { useAvatarStore } from '../../stores/avatarStore'

/** R3F Canvas 错误边界 */
class CanvasErrorBoundary extends Component<
  { fallback: React.ReactNode; children: React.ReactNode },
  { hasError: boolean }
> {
  state = { hasError: false }
  static getDerivedStateFromError() { return { hasError: true } }
  render() {
    if (this.state.hasError) return this.props.fallback
    return this.props.children
  }
}

export default function DigitalHumanStage() {
  const [webglError, setWebglError] = useState(false)
  const { emotion, aiStatus } = useAvatarStore()

  // 检测 WebGL 支持
  useEffect(() => {
    try {
      const c = document.createElement('canvas')
      const gl = c.getContext('webgl2') || c.getContext('webgl')
      if (!gl) setWebglError(true)
    } catch {
      setWebglError(true)
    }
  }, [])

  if (webglError) {
    return <AvatarFallback />
  }

  return (
    <div className="relative w-full flex-1 min-h-0">
      <CanvasErrorBoundary fallback={<AvatarFallback />}>
        <Canvas
          camera={{ position: [0, 0.15, 1.8], fov: 35 }}
          gl={{ antialias: true, alpha: true, preserveDrawingBuffer: false }}
          onCreated={({ gl }) => gl.setClearColor(0x000000, 0)}
          style={{ position: 'absolute', inset: 0 }}
        >
          <Suspense fallback={null}>
            <ambientLight intensity={0.3} />
            <directionalLight position={[2, 3, 2]} intensity={0.5} />
            <pointLight position={[0, 1, 1]} intensity={0.4} color="#6C5CE7" />
            <AvatarHead />
            <AvatarParticles />
            <AvatarHalo />
            <Environment preset="city" environmentIntensity={0.15} />
          </Suspense>
        </Canvas>
      </CanvasErrorBoundary>

      {/* 状态指示器 */}
      <div className="absolute top-4 left-1/2 -translate-x-1/2 flex items-center gap-2 glass rounded-full px-4 py-1.5 z-10">
        <StatusDot status={aiStatus} />
        <span className="text-xs text-text-secondary font-medium">
          {statusLabels[aiStatus] || '等待中'}
        </span>
        <EmotionIcon emotion={emotion} />
      </div>

      {/* 底部渐变遮罩 */}
      <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-[#0a0a1a] to-transparent pointer-events-none" />
    </div>
  )
}

function StatusDot({ status }: { status: string }) {
  const colorMap: Record<string, string> = {
    idle: 'bg-accent',
    listening: 'bg-warning animate-pulse',
    speaking: 'bg-success animate-pulse',
    thinking: 'bg-warning',
    paused: 'bg-text-muted',
    resuming: 'bg-primary-light animate-pulse',
  }
  return <span className={`w-2 h-2 rounded-full ${colorMap[status] || 'bg-accent'}`} />
}

const statusLabels: Record<string, string> = {
  idle: '等待中',
  listening: '正在聆听...',
  speaking: '讲解中...',
  thinking: '思考中...',
  paused: '已暂停',
  resuming: '恢复中...',
}

function EmotionIcon({ emotion }: { emotion: string }) {
  const map: Record<string, string> = {
    friendly: '😊',
    neutral: '😐',
    thinking: '🤔',
    surprised: '😮',
  }
  return <span className="text-xs">{map[emotion] || '😊'}</span>
}
