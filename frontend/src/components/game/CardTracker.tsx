"use client";

import { motion } from "motion/react";
import { useGameStore } from "@/stores/gameStore";

const RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"];
const TOTAL_PER_RANK = 24; // 6 decks x 4 suits

const BAR_HEIGHT_PX = 80; // matches h-20 on mobile; md:h-28 (112px) handled via scale

export function CardTracker() {
  const playedRanks = useGameStore((s) => s.state.shoe.played_ranks) || {};

  const counts = RANKS.map((r) => playedRanks[r] || 0);
  const maxPlayed = Math.max(...counts, 1);

  return (
    <div className="flex flex-col p-3 rounded-[10px] bg-card border border-border">
      <span className="text-xs text-muted-foreground mb-2">Cards Observed</span>
      <div className="flex gap-1" style={{ height: BAR_HEIGHT_PX }}>
        {/* Y-axis labels */}
        <div className="flex flex-col justify-between text-[9px] text-muted-foreground pr-1 pb-4 tabular-nums">
          <span>{maxPlayed}</span>
          <span>{Math.floor(maxPlayed / 2)}</span>
          <span>0</span>
        </div>

        {/* Bars */}
        <div className="flex-1 flex items-end gap-1">
          {RANKS.map((rank) => {
            const played = playedRanks[rank] || 0;
            const ratio = maxPlayed > 0 ? played / maxPlayed : 0;
            const barHeight = Math.round(ratio * BAR_HEIGHT_PX);
            const fillPct = (played / TOTAL_PER_RANK) * 100;

            return (
              <div key={rank} className="flex-1 flex flex-col items-center gap-0.5">
                <motion.div
                  className="w-full rounded-t"
                  initial={{ height: 0 }}
                  animate={{ height: barHeight }}
                  transition={{ type: "spring", stiffness: 200, damping: 20 }}
                  style={{
                    backgroundColor:
                      fillPct > 75
                        ? "var(--color-loss)"
                        : fillPct > 50
                        ? "var(--chart-4)"
                        : "var(--color-profit)",
                  }}
                />
                <span className="text-[9px] text-muted-foreground leading-none">
                  {rank}
                </span>
              </div>
            );
          })}
        </div>
      </div>
      <div className="mt-2 hidden md:flex flex-wrap gap-x-3 gap-y-0.5 text-[10px] text-muted-foreground tabular-nums">
        {RANKS.map((rank) => (
          <span key={rank}>
            {rank}: {playedRanks[rank] || 0}/{TOTAL_PER_RANK}
          </span>
        ))}
      </div>
    </div>
  );
}
