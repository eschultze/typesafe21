"use client";

import { motion, AnimatePresence } from "motion/react";
import { useGameStore } from "@/stores/gameStore";
import { PlayingCard } from "./PlayingCard";
import { Badge } from "@/components/ui/badge";

interface PlayerHandProps {
  playerIndex: number;
}

export function PlayerHand({ playerIndex }: PlayerHandProps) {
  const state = useGameStore((s) => s.state);
  const player = state.players[playerIndex];

  if (!player) return null;

  const isActive = state.current_player === player.name;
  const hand = player.hand;
  const isHuman = player.name === "You";
  const cardCount = hand.cards.length;

  const cardSize = cardCount <= 2 ? "md" : cardCount <= 4 ? "sm" : "sm";

  return (
    <motion.div
      layout
      className={`flex flex-col items-center gap-2 p-3 rounded-xl border transition-all duration-[var(--dur-short)] ${
        isActive
          ? "border-accent/50 bg-accent/5 shadow-[0_0_20px_var(--color-active-glow)]"
          : "border-border bg-card"
      }`}
    >
      <div className="flex items-center gap-2">
        <Badge
          variant={isHuman ? "default" : "secondary"}
          className={isHuman ? "bg-accent text-accent-foreground" : ""}
        >
          {player.name}
        </Badge>
        {hand.is_blackjack && (
          <Badge className="bg-yellow-500 text-black">BJ</Badge>
        )}
        {hand.is_bust && (
          <Badge variant="destructive">Bust</Badge>
        )}
        <motion.span
          key={hand.value}
          initial={{ scale: 1.3 }}
          animate={{ scale: 1 }}
          transition={{ duration: 0.12, ease: [0.16, 1, 0.3, 1] }}
          className="text-lg font-bold tabular-nums"
        >
          {hand.value}
        </motion.span>
      </div>

      <div className="flex gap-1 justify-center flex-wrap">
        <AnimatePresence mode="popLayout">
          {hand.cards.map((card, i) => (
            <PlayingCard
              key={`${card.rank}-${card.suit}-${i}`}
              card={card}
              index={i}
              size={cardSize}
            />
          ))}
        </AnimatePresence>
      </div>

      <div className="flex items-center gap-3 text-xs text-muted-foreground">
        <span>Bet: <span className="font-bold text-foreground tabular-nums">${player.current_bet}</span></span>
        <span>Balance: <span className={`font-bold tabular-nums ${player.balance >= 100 ? "text-[var(--color-profit)]" : "text-[var(--color-loss)]"}`}>${player.balance}</span></span>
        <span className="tabular-nums">{player.wins}W / {player.losses}L / {player.pushes}P</span>
      </div>

      {/* Last 5 rounds */}
      {player.balance_history.length > 1 && (
        <div className="flex gap-1">
          {(() => {
            const h = player.balance_history;
            const start = Math.max(1, h.length - 5);
            const results: string[] = [];
            for (let i = start; i < h.length; i++) {
              if (h[i] > h[i - 1]) results.push("win");
              else if (h[i] < h[i - 1]) results.push("loss");
              else results.push("push");
            }
            return results.map((r, i) => (
              <div
                key={start + i}
                className={`w-2 h-2 rounded-full ${
                  r === "win"
                    ? "bg-[var(--color-profit)]"
                    : r === "loss"
                    ? "bg-[var(--color-loss)]"
                    : "bg-muted-foreground/40"
                }`}
              />
            ));
          })()}
        </div>
      )}
    </motion.div>
  );
}
