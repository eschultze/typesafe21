"use client";

import { motion } from "motion/react";
import { CardData } from "@/stores/gameStore";

const suitColors: Record<string, string> = {
  "♥": "text-red-400",
  "♦": "text-red-400",
  "♣": "text-foreground",
  "♠": "text-foreground",
};

interface PlayingCardProps {
  card: CardData;
  hidden?: boolean;
  index?: number;
  size?: "sm" | "md" | "lg";
}

export function PlayingCard({ card, hidden = false, index = 0, size = "md" }: PlayingCardProps) {
  const dims = {
    sm: "w-10 h-14 text-[10px]",
    md: "w-14 h-[4.5rem] text-xs",
    lg: "w-16 h-[5.5rem] text-sm",
  }[size];

  const isHidden = hidden || card.rank === "?";
  const textColor = suitColors[card.suit] || "text-foreground";

  return (
    <motion.div
      initial={{ opacity: 0, y: 60, rotateZ: -15, scale: 0.7 }}
      animate={{ opacity: 1, y: 0, rotateZ: 0, scale: 1 }}
      transition={{
        type: "spring",
        stiffness: 300,
        damping: 25,
        delay: index * 0.1,
      }}
      className={`${dims} relative select-none rounded-lg border-2 shadow-lg overflow-hidden ${
        isHidden
          ? "border-border bg-[var(--color-card-back)]"
          : "border-border bg-[var(--color-card-face)]"
      }`}
    >
      {isHidden ? (
        <div className="w-full h-full flex items-center justify-center">
          <div className="w-8 h-8 border-2 border-accent/30 rounded-full opacity-50" />
        </div>
      ) : (
        <div className="w-full h-full flex flex-col items-center justify-between p-0.5">
          <span className={`font-bold self-start leading-none ${textColor}`}>
            {card.rank}
          </span>
          <span className={`${size === "sm" ? "text-lg" : "text-xl"} ${textColor}`}>
            {card.suit}
          </span>
          <span className={`font-bold self-end leading-none rotate-180 ${textColor}`}>
            {card.rank}
          </span>
        </div>
      )}
    </motion.div>
  );
}
