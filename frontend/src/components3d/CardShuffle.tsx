"use client";

import { motion, AnimatePresence } from "motion/react";
import { PlayingCard } from "@/components/game/PlayingCard";
import { CardData } from "@/stores/gameStore";
import { useState, useEffect } from "react";

const SAMPLE_CARDS: CardData[] = [
  { rank: "A", suit: "♠", value: 11 },
  { rank: "7", suit: "♥", value: 7 },
  { rank: "K", suit: "♦", value: 10 },
  { rank: "3", suit: "♣", value: 3 },
  { rank: "J", suit: "♥", value: 10 },
  { rank: "5", suit: "♠", value: 5 },
  { rank: "Q", suit: "♦", value: 10 },
  { rank: "9", suit: "♣", value: 9 },
  { rank: "2", suit: "♥", value: 2 },
  { rank: "8", suit: "♠", value: 8 },
  { rank: "10", suit: "♦", value: 10 },
  { rank: "4", suit: "♣", value: 4 },
];

const VISIBLE_CARDS = 7;
const CYCLE_MS = 3000;

export function CardShuffle() {
  const [offset, setOffset] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setOffset((prev) => (prev + 1) % SAMPLE_CARDS.length);
    }, CYCLE_MS);
    return () => clearInterval(timer);
  }, []);

  const visibleCards = Array.from({ length: VISIBLE_CARDS }, (_, i) => {
    const cardIndex = (offset + i) % SAMPLE_CARDS.length;
    return { card: SAMPLE_CARDS[cardIndex], i };
  });

  return (
    <div className="w-full h-full flex items-center justify-center overflow-hidden">
      <div className="relative" style={{ width: VISIBLE_CARDS * 48, height: 120 }}>
        <AnimatePresence mode="popLayout">
          {visibleCards.map(({ card, i }) => {
            const centerIndex = Math.floor(VISIBLE_CARDS / 2);
            const distFromCenter = i - centerIndex;
            const xOffset = distFromCenter * 48;
            const rotation = distFromCenter * 4;
            const scale = 1 - Math.abs(distFromCenter) * 0.06;
            const zIndex = VISIBLE_CARDS - Math.abs(distFromCenter);
            const opacity = 1 - Math.abs(distFromCenter) * 0.12;

            return (
              <motion.div
                key={`${card.rank}-${card.suit}-${offset}-${i}`}
                initial={{ opacity: 0, x: 200, rotateZ: 20, scale: 0.5 }}
                animate={{
                  opacity,
                  x: xOffset,
                  rotateZ: rotation,
                  scale,
                  y: 0,
                }}
                exit={{ opacity: 0, x: -200, rotateZ: -20, scale: 0.5 }}
                transition={{
                  type: "spring",
                  stiffness: 300,
                  damping: 25,
                  delay: i * 0.04,
                }}
                className="absolute top-0 left-1/2"
                style={{
                  marginLeft: -28,
                  zIndex,
                }}
              >
                <PlayingCard card={card} index={i} size="md" />
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </div>
  );
}
