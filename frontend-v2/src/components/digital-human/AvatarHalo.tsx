import { useRef, useMemo } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import { useAvatarStore } from '../../stores/avatarStore'
import { getEmotionColors, getStatusSpeed } from './EmotionController'

export default function AvatarHalo() {
  const ringRef = useRef<THREE.Mesh>(null!)
  const outerRef = useRef<THREE.Mesh>(null!)
  const { emotion, aiStatus } = useAvatarStore()
  const colors = getEmotionColors(emotion)
  const speed = getStatusSpeed(aiStatus)

  const ringMat = useMemo(() => new THREE.MeshBasicMaterial({
    color: new THREE.Color(colors.primary),
    transparent: true,
    opacity: 0.25,
    side: THREE.DoubleSide,
  }), [colors.primary])

  const outerMat = useMemo(() => new THREE.MeshBasicMaterial({
    color: new THREE.Color(colors.accent),
    transparent: true,
    opacity: 0.1,
    side: THREE.DoubleSide,
  }), [colors.accent])

  useFrame((state) => {
    const t = state.clock.getElapsedTime()
    if (ringRef.current) {
      ringRef.current.rotation.z = t * 0.15 * speed
      ringRef.current.rotation.x = Math.sin(t * 0.2) * 0.1
      const pulse = 1 + Math.sin(t * 1.5) * 0.03
      ringRef.current.scale.setScalar(pulse)
    }
    if (outerRef.current) {
      outerRef.current.rotation.z = -t * 0.1 * speed
      outerRef.current.rotation.x = Math.cos(t * 0.25) * 0.08
      outerRef.current.scale.setScalar(1 + Math.sin(t * 2) * 0.04)
    }
  })

  return (
    <group>
      <mesh ref={ringRef} position={[0, -0.35, 0]} rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[0.55, 0.012, 16, 80]} />
        <primitive object={ringMat} attach="material" />
      </mesh>

      <mesh ref={outerRef} position={[0, -0.5, 0]} rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[0.7, 0.006, 8, 64]} />
        <primitive object={outerMat} attach="material" />
      </mesh>

      {/* 底部光点 */}
      <pointLight position={[0, -0.35, 0]} intensity={1.5} distance={1.2} color={colors.accent} />
    </group>
  )
}
