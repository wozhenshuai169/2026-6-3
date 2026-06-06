import { useEffect, useRef } from 'react'

const BARS = 8

interface VoiceWaveformProps {
  active: boolean
  className?: string
}

export default function VoiceWaveform({ active, className = '' }: VoiceWaveformProps) {
  const containerRef = useRef<HTMLDivElement>(null!)

  useEffect(() => {
    if (!active) return
    const bars = containerRef.current.children
    const interval = setInterval(() => {
      for (let i = 0; i < bars.length; i++) {
        const h = active
          ? 4 + Math.random() * 28
          : 2 + Math.random() * 4
        ;(bars[i] as HTMLElement).style.height = `${h}px`
      }
    }, 120)
    return () => clearInterval(interval)
  }, [active])

  return (
    <div ref={containerRef} className={`flex items-end gap-[2px] h-8 ${className}`}>
      {Array.from({ length: BARS }).map((_, i) => (
        <div
          key={i}
          className="w-[3px] rounded-full bg-accent transition-all duration-100"
          style={{
            height: active ? '8px' : '3px',
            opacity: active ? 0.8 : 0.3,
          }}
        />
      ))}
    </div>
  )
}
