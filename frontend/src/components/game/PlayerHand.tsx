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

  return (
    <motion.div
      layout
      className={`flex flex-col items-center gap-2 p-3 rounded-xl border transition-all duration-300 ${
        isActive
          ? "border-green-500/60 bg-green-950/30 shadow-[0_0_20px_rgba(34,197,94,0.15)]"
          : "border-white/10 bg-white/5"
      }`}
    >
      <div className="flex items-center gap-2">
        <Badge
          variant={isHuman ? "default" : "secondary"}
          className={isHuman ? "bg-green-600" : ""}
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
          className="text-lg font-bold"
        >
          {hand.value}
        </motion.span>
      </div>

      <div className="flex gap-1.5">
        <AnimatePresence mode="popLayout">
          {hand.cards.map((card, i) => (
            <PlayingCard
              key={`${card.rank}-${card.suit}-${i}`}
              card={card}
              index={i}
              size="md"
            />
          ))}
        </AnimatePresence>
      </div>

      <div className="flex items-center gap-3 text-xs text-muted-foreground">
        <span>Bet: <span className="font-bold text-foreground">${player.current_bet}</span></span>
        <span>Balance: <span className={`font-bold ${player.balance >= 100 ? "text-green-400" : "text-red-400"}`}>${player.balance}</span></span>
        <span>{player.wins}W / {player.losses}L / {player.pushes}P</span>
      </div>
    </motion.div>
  );
}
