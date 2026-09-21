"use client";

import { Canvas, useFrame } from "@react-three/fiber";
import { useRef, useMemo } from "react";
import * as THREE from "three";

const CARD_COLORS = ["#ef4444", "#3b82f6", "#22c55e", "#eab308", "#a855f7", "#ec4899"];
const TOTAL_CARDS = 12;
const CYCLE = 3.0;

function Card({ index }: { index: number }) {
  const groupRef = useRef<THREE.Group>(null);
  const color = CARD_COLORS[index % CARD_COLORS.length];
  const stagger = index * 0.03;

  useFrame((state) => {
    if (!groupRef.current) return;

    const elapsed = state.clock.elapsedTime;
    const t = ((elapsed + stagger) % CYCLE) / CYCLE;

    const appearEnd = 0.12;
    const holdEnd = 0.45;
    const disappearEnd = 0.55;

    let scale: number;
    if (t < appearEnd) {
      scale = THREE.MathUtils.smoothstep(t / appearEnd, 0, 1);
    } else if (t < holdEnd) {
      scale = 1;
    } else if (t < disappearEnd) {
      scale = 1 - THREE.MathUtils.smoothstep((t - holdEnd) / (disappearEnd - holdEnd), 0, 1);
    } else {
      scale = 0;
    }

    groupRef.current.scale.setScalar(Math.max(0.001, scale));
  });

  const xPos = (index - TOTAL_CARDS / 2) * 0.35;
  const rotZ = (index - TOTAL_CARDS / 2) * 0.06;

  return (
    <group ref={groupRef} position={[xPos, 0, 0]} rotation={[0, 0, rotZ]}>
      <mesh position={[0, 0, 0.005]}>
        <planeGeometry args={[0.55, 0.78]} />
        <meshStandardMaterial color="white" />
      </mesh>
      <mesh position={[0, 0, -0.005]} rotation={[0, Math.PI, 0]}>
        <planeGeometry args={[0.55, 0.78]} />
        <meshStandardMaterial color={color} />
      </mesh>
    </group>
  );
}

export function CardShuffle() {
  const cards = useMemo(() => Array.from({ length: TOTAL_CARDS }, (_, i) => i), []);

  return (
    <Canvas camera={{ position: [0, 0, 3.5], fov: 40 }}>
      <ambientLight intensity={0.8} />
      <pointLight position={[3, 3, 5]} intensity={0.6} />
      {cards.map((i) => (
        <Card key={i} index={i} />
      ))}
    </Canvas>
  );
}
