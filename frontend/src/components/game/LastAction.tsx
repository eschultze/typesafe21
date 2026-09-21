"use client";

import { motion, AnimatePresence } from "motion/react";
import { useGameStore } from "@/stores/gameStore";
import { Badge } from "@/components/ui/badge";

export function LastAction() {
  const lastAction = useGameStore((s) => s.state.last_action);

  if (!lastAction || lastAction.type !== "round_result") return null;

  const { bets, result } = lastAction;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        className="w-full p-4 rounded-xl bg-white/5 border border-white/10"
      >
        <div className="text-xs text-muted-foreground mb-2">Round Result</div>
        <div className="flex flex-wrap gap-2">
          {result.hands.map((h: any, i: number) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.1 }}
              className="flex items-center gap-2"
            >
              <Badge
                variant={
                  h.result === "win"
                    ? "default"
                    : h.result === "push"
                    ? "secondary"
                    : "destructive"
                }
                className={
                  h.result === "win"
                    ? "bg-green-600"
                    : h.result === "push"
                    ? "bg-yellow-600"
                    : ""
                }
              >
                {h.name}: {h.result?.toUpperCase()}
              </Badge>
              {h.is_ai && h.decision && (
                <span className="text-xs text-muted-foreground">
                  ({h.decision}, conf: {(h.confidence * 100).toFixed(0)}%)
                </span>
              )}
            </motion.div>
          ))}
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
