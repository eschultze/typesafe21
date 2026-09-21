"use client";

import { motion } from "motion/react";
import { useGameStore } from "@/stores/gameStore";

export function Scoreboard() {
  const players = useGameStore((s) => s.state.players);

  if (players.length === 0) return null;

  return (
    <div className="flex gap-3">
      {players.map((p) => {
        const profit = p.balance - 100;
        return (
          <motion.div
            key={p.name}
            layout
            className="flex flex-col items-center p-3 rounded-lg bg-white/5 border border-white/10 min-w-[100px]"
          >
            <span className="text-xs text-muted-foreground mb-1">{p.name}</span>
            <motion.span
              key={p.balance}
              initial={{ scale: 1.2 }}
              animate={{ scale: 1 }}
              className={`text-xl font-bold ${
                profit > 0 ? "text-green-400" : profit < 0 ? "text-red-400" : "text-white"
              }`}
            >
              ${p.balance}
            </motion.span>
            <span className={`text-xs ${profit >= 0 ? "text-green-500" : "text-red-500"}`}>
              {profit >= 0 ? "+" : ""}{profit}
            </span>
          </motion.div>
        );
      })}
    </div>
  );
}
