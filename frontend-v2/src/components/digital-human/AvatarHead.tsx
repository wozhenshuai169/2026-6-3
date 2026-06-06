import { useRef, useMemo } from 'react'
import { useFrame } from '@react-three/fiber'
import { Float } from '@react-three/drei'
import * as THREE from 'three'
import { useAvatarStore } from '../../stores/avatarStore'
import { getEmotionColors, getStatusSpeed } from './EmotionController'

export default function AvatarHead() {
  const groupRef = useRef<THREE.Group>(null!)
  const headRef = useRef<THREE.Mesh>(null!)
  const leftEyeRef = useRef<THREE.Mesh>(null!)
  const rightEyeRef = useRef<THREE.Mesh>(null!)
  const mouthRef = useRef<THREE.Mesh>(null!)
  const wireRef = useRef<THREE.Mesh>(null!)

  const { emotion, aiStatus } = useAvatarStore()
  const colors = useMemo(() => getEmotionColors(emotion), [emotion])
  const speed = useMemo(() => getStatusSpeed(aiStatus), [aiStatus])

  // 面部材质
  const faceMat = useMemo(() => new THREE.MeshPhysicalMaterial({
    color: new THREE.Color(colors.primary),
    emissive: new THREE.Color(colors.primary),
    emissiveIntensity: 0.15,
    roughness: 0.3,
    metalness: 0.1,
    transparent: true,
    opacity: 0.85,
    clearcoat: 0.3,
  }), [colors.primary])

  const wireMat = useMemo(() => new THREE.MeshBasicMaterial({
    color: new THREE.Color(colors.accent),
    wireframe: true,
    transparent: true,
    opacity: 0.08,
  }), [colors.accent])

  const eyeMat = useMemo(() => new THREE.MeshStandardMaterial({
    color: new THREE.Color(colors.accent),
    emissive: new THREE.Color(colors.accent),
    emissiveIntensity: 1.5,
    roughness: 0.1,
  }), [colors.accent])

  const mouthMat = useMemo(() => new THREE.MeshStandardMaterial({
    color: new THREE.Color(colors.accent),
    emissive: new THREE.Color(colors.accent),
    emissiveIntensity: 0.6,
    roughness: 0.2,
  }), [colors.accent])

  useFrame((state) => {
    const t = state.clock.getElapsedTime()

    // 整体微浮动
    groupRef.current.position.y = Math.sin(t * 0.5) * 0.08

    // 头部微旋转（随情绪）
    const lookAmount = aiStatus === 'thinking' ? 0.12 : 0.03
    headRef.current.rotation.y = Math.sin(t * 0.3) * lookAmount
    headRef.current.rotation.x = Math.sin(t * 0.4) * lookAmount * 0.6

    // 口型动画（speaking 时开合）
    if (mouthRef.current) {
      const targetScale = aiStatus === 'speaking'
        ? 0.5 + Math.abs(Math.sin(t * 8 + Math.sin(t * 3) * 2)) * 0.5
        : 0.3
      mouthRef.current.scale.x += (targetScale - mouthRef.current.scale.x) * 0.3
      mouthRef.current.scale.y += (targetScale * 0.4 - mouthRef.current.scale.y) * 0.3
    }

    // 眨眼
    const blinkPhase = Math.sin(t * 0.13) * 0.5 + 0.5
    const isBlinking = blinkPhase > 0.95
    const eyeScaleY = isBlinking ? 0.08 : 1
    if (leftEyeRef.current) leftEyeRef.current.scale.y += (eyeScaleY - leftEyeRef.current.scale.y) * 0.4
    if (rightEyeRef.current) rightEyeRef.current.scale.y += (eyeScaleY - rightEyeRef.current.scale.y) * 0.4

    // wireframe 旋转
    if (wireRef.current) {
      wireRef.current.rotation.y += 0.002 * speed
    }
  })

  return (
    <Float speed={speed * 2} rotationIntensity={0.05} floatIntensity={0.08}>
      <group ref={groupRef}>
        {/* 头部 */}
        <mesh ref={headRef} material={faceMat} position={[0, 0.05, 0]}>
          <sphereGeometry args={[0.52, 64, 48, 0, Math.PI * 2, 0, Math.PI * 0.85]} />
        </mesh>

        {/* Wireframe 覆盖层 */}
        <mesh ref={wireRef} material={wireMat} position={[0, 0.05, 0]}>
          <sphereGeometry args={[0.525, 32, 24, 0, Math.PI * 2, 0, Math.PI * 0.85]} />
        </mesh>

        {/* 左眼 */}
        <mesh ref={leftEyeRef} material={eyeMat} position={[-0.16, 0.28, 0.43]}>
          <sphereGeometry args={[0.06, 16, 16]} />
        </mesh>
        <mesh material={eyeMat} position={[-0.16, 0.28, 0.47]}>
          <sphereGeometry args={[0.025, 8, 8]} />
        </mesh>

        {/* 右眼 */}
        <mesh ref={rightEyeRef} material={eyeMat} position={[0.16, 0.28, 0.43]}>
          <sphereGeometry args={[0.06, 16, 16]} />
        </mesh>
        <mesh material={eyeMat} position={[0.16, 0.28, 0.47]}>
          <sphereGeometry args={[0.025, 8, 8]} />
        </mesh>

        {/* 嘴部光环 */}
        <mesh ref={mouthRef} material={mouthMat} position={[0, 0.02, 0.48]}>
          <torusGeometry args={[0.1, 0.018, 8, 24]} />
        </mesh>

        {/* 光点 — 眉心 */}
        <pointLight
          position={[0, 0.38, 0.48]}
          intensity={2}
          distance={0.5}
          color={colors.accent}
        />
      </group>
    </Float>
  )
}
