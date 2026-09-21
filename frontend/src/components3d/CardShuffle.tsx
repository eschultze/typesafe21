"use client";

import { Canvas, useFrame } from "@react-three/fiber";
import { useRef, useMemo } from "react";
import * as THREE from "three";

function Card({ index, total }: { index: number; total: number }) {
  const meshRef = useRef<THREE.Mesh>(null);
  const startTime = useMemo(() => Date.now() + index * 80, [index]);

  useFrame(() => {
    if (!meshRef.current) return;
    const elapsed = (Date.now() - startTime) / 1000;
    const t = Math.max(0, Math.min(1, elapsed / 0.8));

    const startX = -3 + (index / total) * 6;
    const startY = 3;
    const startZ = -2;
    const endX = (index - total / 2) * 0.3;
    const endY = -0.5;
    const endZ = 0;

    meshRef.current.position.x = THREE.MathUtils.lerp(startX, endX, t);
    meshRef.current.position.y = THREE.MathUtils.lerp(startY, endY, t) + Math.sin(t * Math.PI) * 0.5;
    meshRef.current.position.z = THREE.MathUtils.lerp(startZ, endZ, t);

    meshRef.current.rotation.x = THREE.MathUtils.lerp(-0.5, 0, t);
    meshRef.current.rotation.z = THREE.MathUtils.lerp(
      (index - total / 2) * 0.15,
      (index - total / 2) * 0.05,
      t
    );
  });

  const colors = ["#ef4444", "#3b82f6", "#22c55e", "#eab308", "#a855f7", "#ec4899"];
  const color = colors[index % colors.length];

  return (
    <mesh ref={meshRef} position={[0, 3, -2]}>
      <boxGeometry args={[0.6, 0.85, 0.01]} />
      <meshStandardMaterial color={color} />
    </mesh>
  );
}

function CardStack() {
  const cards = useMemo(() => Array.from({ length: 12 }, (_, i) => i), []);

  return (
    <>
      {cards.map((i) => (
        <Card key={i} index={i} total={cards.length} />
      ))}
    </>
  );
}

export function CardShuffle() {
  return (
    <Canvas camera={{ position: [0, 1, 4], fov: 50 }}>
      <ambientLight intensity={0.5} />
      <pointLight position={[5, 5, 5]} intensity={1} />
      <pointLight position={[-5, 3, -5]} intensity={0.3} color="#3b82f6" />
      <CardStack />
    </Canvas>
  );
}
