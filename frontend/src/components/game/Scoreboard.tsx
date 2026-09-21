"use client";

import { motion } from "motion/react";
import { useGameStore } from "@/stores/gameStore";

export function Scoreboard() {
  const players = useGameStore((s) => s.state.players);

  if (players.length === 0) return null;

  return (
    <div className="grid grid-cols-3 gap-2 md:gap-3 w-full">
      {players.map((p) => {
        const startingBalance = p.balance_history[0] ?? 100;
        const profit = p.balance - startingBalance;
        return (
          <motion.div
            key={p.name}
            layout
            className="flex flex-col items-center p-3 rounded-[10px] bg-card border border-border min-w-[100px] flex-1"
          >
            <span className="text-xs text-muted-foreground mb-1">{p.name}</span>
            <motion.span
              key={p.balance}
              initial={{ scale: 1.2 }}
              animate={{ scale: 1 }}
              transition={{ duration: 0.12, ease: [0.16, 1, 0.3, 1] }}
              className={`text-xl font-bold tabular-nums ${
                profit > 0 ? "text-[var(--color-profit)]" : profit < 0 ? "text-[var(--color-loss)]" : "text-foreground"
              }`}
            >
              ${p.balance}
            </motion.span>
            <span className={`text-xs tabular-nums ${profit >= 0 ? "text-[var(--color-profit)]" : "text-[var(--color-loss)]"}`}>
              {profit >= 0 ? "+" : ""}{profit}
            </span>
          </motion.div>
        );
      })}
    </div>
  );
}
