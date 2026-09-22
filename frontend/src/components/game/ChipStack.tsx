"use client";

import { useGameStore } from "@/stores/gameStore";
import { motion, AnimatePresence } from "motion/react";

const DENOM_COLORS: Record<number, { bg: string; label: string }> = {
  25: { bg: "#22c55e", label: "$25" },
  10: { bg: "#3b82f6", label: "$10" },
  5:  { bg: "#ef4444", label: "$5" },
  1:  { bg: "#a855f7", label: "$1" },
};

const CHIP_ORDER = [25, 10, 5, 1];
const MAX_CHIPS = 6;

function breakIntoChips(bet: number): number[] {
  const chips: number[] = [];
  let remaining = bet;
  for (const denom of CHIP_ORDER) {
    while (remaining >= denom && chips.length < MAX_CHIPS) {
      chips.push(denom);
      remaining -= denom;
    }
  }
  if (remaining > 0 && chips.length < MAX_CHIPS) chips.push(remaining);
  return chips;
}

function Chip({
  denom,
  index,
  animating,
  speed,
}: {
  denom: number;
  index: number;
  animating: boolean;
  speed: number;
}) {
  const { bg, label } = DENOM_COLORS[denom] || { bg: "#888", label: `$${denom}` };

  return (
    <motion.div
      key={`${denom}-${index}`}
      initial={animating ? { rotateY: 90, scale: 0 } : false}
      animate={{ rotateY: 0, scale: 1 }}
      transition={{
        type: "spring",
        stiffness: 300 * speed,
        damping: 20,
        delay: index * 0.06 * (1 / speed),
      }}
      className="chip"
      style={{
        backgroundColor: bg,
        "--chip-index": index,
        zIndex: index,
      } as React.CSSProperties}
      title={label}
    />
  );
}

function PlayerChips({
  bet,
  animating,
  autoPlay,
  playerName,
  isHero,
}: {
  bet: number;
  animating: boolean;
  autoPlay: boolean;
  playerName: string;
  isHero: boolean;
}) {
  const chips = breakIntoChips(bet);
  const speed = autoPlay ? 2 : 1;

  if (chips.length === 0) return <div className="chip-slot-empty" />;

  return (
    <div className={`chip-player-col ${isHero ? "chip-hero" : ""}`}>
      <AnimatePresence mode="popLayout">
        {chips.map((denom, i) => (
          <Chip
            key={`${denom}-${i}`}
            denom={denom}
            index={i}
            animating={animating}
            speed={speed}
          />
        ))}
      </AnimatePresence>
      <span className="chip-total">${bet}</span>
    </div>
  );
}

export function ChipStack() {
  const players = useGameStore((s) => s.state.players);
  const animating = useGameStore((s) => s.chipsAnimating);
  const autoPlay = useGameStore((s) => s.state.auto_play);

  if (players.length === 0 || players.every((p) => p.current_bet === 0)) {
    return null;
  }

  return (
    <div className="chip-container">
      {players.map((p, i) => (
        <PlayerChips
          key={p.name}
          bet={p.current_bet}
          animating={animating}
          autoPlay={autoPlay}
          playerName={p.name}
          isHero={i === 0}
        />
      ))}
    </div>
  );
}
