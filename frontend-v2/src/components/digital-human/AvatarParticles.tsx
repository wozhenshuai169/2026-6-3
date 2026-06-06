import { useRef, useMemo } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import { useAvatarStore } from '../../stores/avatarStore'
import { getEmotionColors, getStatusSpeed } from './EmotionController'

const PARTICLE_COUNT = 40

export default function AvatarParticles() {
  const groupRef = useRef<THREE.Group>(null!)
  const { emotion, aiStatus } = useAvatarStore()
  const colors = getEmotionColors(emotion)
  const speed = getStatusSpeed(aiStatus)

  const particles = useMemo(() => {
    return Array.from({ length: PARTICLE_COUNT }, (_, i) => {
      const angle = (i / PARTICLE_COUNT) * Math.PI * 2
      const radius = 0.65 + Math.random() * 0.3
      const height = (Math.random() - 0.5) * 0.8
      const phase = Math.random() * Math.PI * 2
      return { angle, radius, height, phase, baseSpeed: 0.1 + Math.random() * 0.3 }
    })
  }, [])

  useFrame((state) => {
    const t = state.clock.getElapsedTime()
    particles.forEach((p, i) => {
      const child = groupRef.current.children[i] as THREE.Mesh
      if (!child) return

      const currentAngle = p.angle + t * p.baseSpeed * speed * 2
      child.position.x = Math.cos(currentAngle) * p.radius
      child.position.z = Math.sin(currentAngle) * (p.radius * 0.6)
      child.position.y = p.height + Math.sin(t * 0.8 + p.phase) * 0.1

      // 脉冲大小
      const pulse = 0.6 + Math.sin(t * 2 + p.phase) * 0.4
      child.scale.setScalar(pulse)
    })
    groupRef.current.rotation.y += 0.001 * speed
  })

  return (
    <group ref={groupRef}>
      {particles.map((_, i) => (
        <mesh key={i}>
          <sphereGeometry args={[0.012, 4, 4]} />
          <meshBasicMaterial
            color={new THREE.Color(colors.accent)}
            transparent
            opacity={0.6}
          />
        </mesh>
      ))}
    </group>
  )
}
