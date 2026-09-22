"use client";

import { motion } from "motion/react";
import { useGameStore } from "@/stores/gameStore";

function ScoreLine({ history }: { history: number[] }) {
  if (history.length < 2) return null;

  const w = 200;
  const h = 60;
  const pad = 4;

  const min = history.length > 0 ? Math.min(...history.slice(-500)) : 0;
  const max = history.length > 0 ? Math.max(...history.slice(-500)) : 100;
  const range = max - min || 1;

  const points = history.map((v, i) => {
    const x = pad + (i / (history.length - 1)) * (w - pad * 2);
    const y = h - pad - ((v - min) / range) * (h - pad * 2);
    return `${x},${y}`;
  });

  const profit = history[history.length - 1] >= history[0];
  const color = profit ? "var(--color-profit)" : "var(--color-loss)";

  return (
    <svg
      viewBox={`0 0 ${w} ${h}`}
      className="absolute inset-0 w-full h-full pointer-events-none"
      preserveAspectRatio="none"
      aria-hidden
    >
      <defs>
        <filter id={`score-glow-${profit ? "w" : "l"}`}>
          <feGaussianBlur stdDeviation="2.5" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      <polyline
        points={points.join(" ")}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity="0.18"
        filter={`url(#score-glow-${profit ? "w" : "l"})`}
      />
    </svg>
  );
}

export function Scoreboard() {
  const players = useGameStore((s) => s.state.players);

  if (players.length === 0) return null;

  return (
    <div className="grid grid-cols-2 gap-2 md:gap-3 w-full">
      {players.map((p) => {
        const startingBalance = p.balance_history[0] ?? 100;
        const profit = p.balance - startingBalance;
        return (
          <motion.div
            key={p.name}
            layout
            className="relative flex flex-col items-center p-3 rounded-[10px] bg-card border border-border min-w-[100px] flex-1 overflow-hidden"
          >
            <ScoreLine history={p.balance_history} />
            <span className="relative text-xs text-muted-foreground mb-1 z-10">{p.name}</span>
            <motion.span
              key={p.balance}
              initial={{ scale: 1.2 }}
              animate={{ scale: 1 }}
              transition={{ duration: 0.12, ease: [0.16, 1, 0.3, 1] }}
              className={`relative text-xl font-bold tabular-nums z-10 ${
                profit > 0 ? "text-[var(--color-profit)]" : profit < 0 ? "text-[var(--color-loss)]" : "text-foreground"
              }`}
            >
              ${p.balance}
            </motion.span>
            <span className={`relative text-xs tabular-nums z-10 ${profit >= 0 ? "text-[var(--color-profit)]" : "text-[var(--color-loss)]"}`}>
              {profit >= 0 ? "+" : ""}{profit}
            </span>
          </motion.div>
        );
      })}
    </div>
  );
}
