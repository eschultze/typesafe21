"use client";

import { motion } from "motion/react";
import { CardData } from "@/stores/gameStore";

const suitColors: Record<string, string> = {
  "♥": "text-red-500",
  "♦": "text-red-500",
  "♣": "text-white",
  "♠": "text-white",
};

interface PlayingCardProps {
  card: CardData;
  hidden?: boolean;
  index?: number;
  size?: "sm" | "md" | "lg";
}

export function PlayingCard({ card, hidden = false, index = 0, size = "md" }: PlayingCardProps) {
  const dims = {
    sm: "w-12 h-16 text-xs",
    md: "w-16 h-22 text-sm",
    lg: "w-20 h-28 text-base",
  }[size];

  const isHidden = hidden || card.rank === "?";

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
      className={`${dims} relative select-none`}
      style={{ perspective: 800 }}
    >
      <motion.div
        className="w-full h-full relative"
        animate={{ rotateY: isHidden ? 180 : 0 }}
        transition={{ duration: 0.5 }}
        style={{ transformStyle: "preserve-3d" }}
      >
        {/* Front face */}
        <div
          className={`absolute inset-0 rounded-lg border-2 flex flex-col items-center justify-between p-1 ${
            isHidden
              ? "border-gray-600 bg-gradient-to-br from-blue-800 to-blue-950"
              : "border-gray-300 bg-white shadow-lg"
          }`}
          style={{ backfaceVisibility: "hidden" }}
        >
          {!isHidden && (
            <>
              <span className={`font-bold self-start leading-none ${suitColors[card.suit] || "text-white"}`}>
                {card.rank}
              </span>
              <span className={`text-2xl ${suitColors[card.suit] || "text-white"}`}>
                {card.suit}
              </span>
              <span className={`font-bold self-end leading-none rotate-180 ${suitColors[card.suit] || "text-white"}`}>
                {card.rank}
              </span>
            </>
          )}
        </div>

        {/* Back face */}
        <div
          className="absolute inset-0 rounded-lg border-2 border-gray-600 bg-gradient-to-br from-blue-800 to-blue-950 flex items-center justify-center"
          style={{ backfaceVisibility: "hidden", transform: "rotateY(180deg)" }}
        >
          <div className="w-8 h-8 border-2 border-blue-400 rounded-full opacity-50" />
        </div>
      </motion.div>
    </motion.div>
  );
}
