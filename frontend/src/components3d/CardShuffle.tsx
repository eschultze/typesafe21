"use client";

import { Canvas, useFrame } from "@react-three/fiber";
import { useRef, useMemo } from "react";
import * as THREE from "three";

const CARD_COLORS = ["#ef4444", "#3b82f6", "#22c55e", "#eab308", "#a855f7", "#ec4899"];
const TOTAL_CARDS = 12;
const CYCLE_DURATION = 3.0;
const APPEAR_DURATION = 0.3;
const HOLD_DURATION = 1.0;
const DISAPPEAR_DURATION = 0.25;
const PAUSE_DURATION = 0.8;

function Card({ index }: { index: number }) {
  const groupRef = useRef<THREE.Group>(null);
  const frontRef = useRef<THREE.Mesh>(null);
  const backRef = useRef<THREE.Mesh>(null);

  const color = CARD_COLORS[index % CARD_COLORS.length];
  const staggerDelay = index * 0.03;

  const materials = useMemo(() => {
    const frontMat = new THREE.MeshStandardMaterial({
      color: 0xffffff,
      side: THREE.FrontSide,
    });
    const backMat = new THREE.MeshStandardMaterial({
      color: color,
      side: THREE.FrontSide,
    });
    const edgeMat = new THREE.MeshStandardMaterial({ color: 0x888888 });
    return { frontMat, backMat, edgeMat };
  }, [color]);

  useFrame((state) => {
    if (!groupRef.current) return;

    const elapsed = state.clock.elapsedTime;
    const t = ((elapsed + staggerDelay) % CYCLE_DURATION) / CYCLE_DURATION;

    let scale: number;
    if (t < APPEAR_DURATION / CYCLE_DURATION) {
      // Appearing
      const p = t / (APPEAR_DURATION / CYCLE_DURATION);
      scale = THREE.MathUtils.smoothstep(p, 0, 1);
    } else if (t < (APPEAR_DURATION + HOLD_DURATION) / CYCLE_DURATION) {
      // Holding
      scale = 1;
    } else if (t < (APPEAR_DURATION + HOLD_DURATION + DISAPPEAR_DURATION) / CYCLE_DURATION) {
      // Disappearing
      const p = (t - (APPEAR_DURATION + HOLD_DURATION) / CYCLE_DURATION) / (DISAPPEAR_DURATION / CYCLE_DURATION);
      scale = 1 - THREE.MathUtils.smoothstep(p, 0, 1);
    } else {
      // Paused
      scale = 0;
    }

    groupRef.current.scale.setScalar(scale);
  });

  const xPos = (index - TOTAL_CARDS / 2) * 0.35;
  const rotZ = (index - TOTAL_CARDS / 2) * 0.06;

  return (
    <group ref={groupRef} position={[xPos, 0, 0]} rotation={[0, 0, rotZ]}>
      {/* Front face */}
      <mesh ref={frontRef} position={[0, 0, 0.006]}>
        <planeGeometry args={[0.55, 0.78]} />
        <primitive object={materials.frontMat} attach="material" />
      </mesh>
      {/* Back face */}
      <mesh ref={backRef} position={[0, 0, -0.006]} rotation={[0, Math.PI, 0]}>
        <planeGeometry args={[0.55, 0.78]} />
        <primitive object={materials.backMat} attach="material" />
      </mesh>
      {/* Edge */}
      <mesh>
        <boxGeometry args={[0.55, 0.78, 0.012]} />
        <primitive object={materials.edgeMat} attach="material" />
      </mesh>
    </group>
  );
}

function CardFan() {
  const cards = useMemo(() => Array.from({ length: TOTAL_CARDS }, (_, i) => i), []);

  return (
    <>
      {cards.map((i) => (
        <Card key={i} index={i} />
      ))}
    </>
  );
}

export function CardShuffle() {
  return (
    <Canvas
      camera={{ position: [0, 0, 3.5], fov: 40 }}
      frameloop="demand"
      style={{ background: "transparent" }}
    >
      <ambientLight intensity={0.7} />
      <pointLight position={[3, 3, 5]} intensity={0.8} />
      <pointLight position={[-3, 2, -3]} intensity={0.3} color="#3b82f6" />
      <CardFan />
    </Canvas>
  );
}
