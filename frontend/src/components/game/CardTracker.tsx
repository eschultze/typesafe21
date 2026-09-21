"use client";

import { motion } from "motion/react";
import { useGameStore } from "@/stores/gameStore";

const RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"];

const TOTAL_PER_RANK = 24; // 6 decks × 4 suits

export function CardTracker() {
  const playedRanks = useGameStore((s) => s.state.shoe.played_ranks);

  const maxPlayed = Math.max(...RANKS.map((r) => playedRanks[r] || 0), 1);

  return (
    <div className="flex flex-col p-3 rounded-lg bg-white/5 border border-white/10">
      <span className="text-xs text-muted-foreground mb-2">Cards Observed</span>
      <div className="flex items-end gap-1 h-24">
        {RANKS.map((rank) => {
          const played = playedRanks[rank] || 0;
          const remaining = TOTAL_PER_RANK - played;
          const pct = (played / TOTAL_PER_RANK) * 100;

          return (
            <div key={rank} className="flex-1 flex flex-col items-center gap-0.5">
              <motion.div
                className="w-full rounded-t"
                initial={{ height: 0 }}
                animate={{ height: `${(played / maxPlayed) * 100}%` }}
                transition={{ type: "spring", stiffness: 200, damping: 20 }}
                style={{
                  backgroundColor:
                    pct > 75
                      ? "#ef4444"
                      : pct > 50
                      ? "#eab308"
                      : "#22c55e",
                  minHeight: played > 0 ? "2px" : "0px",
                }}
              />
              <span className="text-[9px] text-muted-foreground leading-none">
                {rank}
              </span>
            </div>
          );
        })}
      </div>
      <div className="mt-2 flex flex-wrap gap-x-3 gap-y-0.5 text-[10px] text-muted-foreground">
        {RANKS.map((rank) => (
          <span key={rank}>
            {rank}: {playedRanks[rank] || 0}/{TOTAL_PER_RANK}
          </span>
        ))}
      </div>
    </div>
  );
}
