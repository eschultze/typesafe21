"use client";

import dynamic from "next/dynamic";

const CardShuffle = dynamic(
  () => import("@/components3d/CardShuffle").then((m) => m.CardShuffle),
  { ssr: false }
);

import { useGameStore } from "@/stores/gameStore";

export function HeroScene() {
  const roundNumber = useGameStore((s) => s.state.round_number);

  if (roundNumber > 0) return null;

  return (
    <div className="w-full h-48 relative">
      <CardShuffle />
    </div>
  );
}
