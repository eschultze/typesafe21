"use client";

import { Canvas, useFrame } from "@react-three/fiber";
import { useRef, useMemo, useEffect } from "react";
import * as THREE from "three";

const CHIP_COLORS: Record<number, string> = {
  25: "#22c55e",
  10: "#3b82f6",
  5: "#ef4444",
};
const CHIP_RADIUS = 0.28;
const CHIP_HEIGHT = 0.1;
const CHIP_GAP = 0.12;
const MAX_CHIPS = 6;

function breakIntoChips(bet: number): number[] {
  const chips: number[] = [];
  let remaining = bet;
  for (const denom of [25, 10, 5]) {
    while (remaining >= denom && chips.length < MAX_CHIPS) {
      chips.push(denom);
      remaining -= denom;
    }
  }
  if (remaining > 0 && chips.length < MAX_CHIPS) {
    chips.push(remaining);
  }
  return chips;
}

function Chip({
  denom,
  index,
  animate,
  speed,
}: {
  denom: number;
  index: number;
  animate: boolean;
  speed: number;
}) {
  const meshRef = useRef<THREE.Mesh>(null);
  const targetScale = useRef(0);
  const currentScale = useRef(0);

  const color = CHIP_COLORS[denom] || "#888888";

  useEffect(() => {
    targetScale.current = animate ? 1 : 0;
  }, [animate]);

  useFrame((_, delta) => {
    if (!meshRef.current) return;
    const target = targetScale.current;
    const step = delta * speed * 8;
    currentScale.current += (target - currentScale.current) * Math.min(step, 1);
    if (Math.abs(currentScale.current - target) < 0.001) {
      currentScale.current = target;
    }
    meshRef.current.scale.setScalar(currentScale.current);
  });

  return (
    <mesh
      ref={meshRef}
      position={[0, index * CHIP_GAP, 0]}
      scale={0}
    >
      <cylinderGeometry args={[CHIP_RADIUS, CHIP_RADIUS, CHIP_HEIGHT, 24]} />
      <meshStandardMaterial color={color} />
    </mesh>
  );
}

function ChipStack({
  position,
  bet,
  animating,
  speed,
}: {
  position: [number, number, number];
  bet: number;
  animating: boolean;
  speed: number;
}) {
  const chips = useMemo(() => breakIntoChips(bet), [bet]);

  return (
    <group position={position}>
      {chips.map((denom, i) => (
        <Chip
          key={`${denom}-${i}`}
          denom={denom}
          index={i}
          animate={animating}
          speed={speed}
        />
      ))}
    </group>
  );
}

export function ChipScene({
  bets,
  animating,
  autoPlay,
}: {
  bets: number[];
  animating: boolean;
  autoPlay: boolean;
}) {
  const speed = autoPlay ? 2.0 : 1.0;

  return (
    <Canvas
      camera={{ position: [0, 1.5, 4], fov: 35 }}
      style={{ background: "transparent" }}
    >
      <ambientLight intensity={0.6} />
      <pointLight position={[2, 4, 3]} intensity={0.8} />
      <ChipStack position={[-1.8, -0.5, 0]} bet={bets[0] || 0} animating={animating} speed={speed} />
      <ChipStack position={[0, -0.5, 0]} bet={bets[1] || 0} animating={animating} speed={speed} />
      <ChipStack position={[1.8, -0.5, 0]} bet={bets[2] || 0} animating={animating} speed={speed} />
    </Canvas>
  );
}
