"use client";

import { motion, AnimatePresence } from "motion/react";
import { useGameStore } from "@/stores/gameStore";
import { PlayingCard } from "./PlayingCard";
import { Badge } from "@/components/ui/badge";

export function DealerHand() {
  const { dealer, dealer_hidden, phase } = useGameStore((s) => s.state);

  if (!dealer || dealer.cards.length === 0) return null;

  const showAll = !dealer_hidden || phase === "results" || phase === "dealer_turn";
  const cardCount = dealer.cards.length;
  const cardSize = cardCount <= 3 ? "lg" : "md";

  return (
    <div className="flex flex-col items-center gap-3">
      <div className="flex items-center gap-2">
        <Badge variant="secondary" className="text-sm">
          Dealer
        </Badge>
        {showAll && (
          <motion.span
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-lg font-bold"
          >
            {dealer.value}
          </motion.span>
        )}
        {dealer.is_blackjack && (
          <Badge className="bg-yellow-500 text-black">Blackjack!</Badge>
        )}
        {dealer.is_bust && (
          <Badge variant="destructive">Bust!</Badge>
        )}
      </div>
      <div className="flex gap-1.5 justify-center flex-wrap">
        <AnimatePresence mode="popLayout">
          {dealer.cards.map((card, i) => (
            <PlayingCard
              key={`${card.rank}-${card.suit}-${i}`}
              card={card}
              hidden={i === 1 && !showAll}
              index={i}
              size={cardSize}
            />
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}
