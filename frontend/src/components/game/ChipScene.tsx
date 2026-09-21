"use client";

import dynamic from "next/dynamic";
import { useGameStore } from "@/stores/gameStore";

const ChipStack3D = dynamic(
  () => import("@/components3d/ChipStack3D").then((m) => m.ChipScene),
  { ssr: false }
);

export function ChipScene() {
  const players = useGameStore((s) => s.state.players);
  const animating = useGameStore((s) => s.chipsAnimating);
  const autoPlay = useGameStore((s) => s.state.auto_play);

  const bets = players.map((p) => p.current_bet);

  // Don't render if no bets placed yet
  if (bets.every((b) => b === 0)) return null;

  return (
    <div className="w-full h-16 relative -mt-2">
      <ChipStack3D bets={bets} animating={animating} autoPlay={autoPlay} />
    </div>
  );
}
