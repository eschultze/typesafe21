"use client";

import { useEffect, useRef } from "react";
import { useGameStore } from "@/stores/gameStore";

export function WinSound() {
  const lastAction = useGameStore((s) => s.state.last_action);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    audioRef.current = new Audio("/cash_register.mp3");
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (!lastAction || lastAction.type !== "round_result") return;

    const { result } = lastAction;
    const anyAIWon = result?.hands?.some(
      (h) => h.is_ai && h.result === "win"
    );

    if (anyAIWon && audioRef.current) {
      audioRef.current.currentTime = 0;
      audioRef.current.play().catch(() => {});
    }
  }, [lastAction]);

  return null;
}
