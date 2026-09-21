"use client";

import { useGameStore } from "@/stores/gameStore";

export function StatsPanel() {
  const aiBetHistory = useGameStore((s) => s.ai_bet_history);
  const aiConfidenceHistory = useGameStore((s) => s.ai_confidence_history);

  const avgBet =
    aiBetHistory.length > 0
      ? Math.round(aiBetHistory.reduce((a, b) => a + b, 0) / aiBetHistory.length)
      : 0;

  const avgConfidence =
    aiConfidenceHistory.length > 0
      ? (
          aiConfidenceHistory.reduce((a, b) => a + b, 0) /
          aiConfidenceHistory.length *
          100
        ).toFixed(1)
      : "0.0";

  const totalRounds = aiBetHistory.length;

  return (
    <div className="flex flex-col p-3 rounded-lg bg-white/5 border border-white/10">
      <span className="text-xs text-muted-foreground mb-2">AI Statistics</span>
      <div className="grid grid-cols-3 gap-4 text-center">
        <div className="flex flex-col">
          <span className="text-2xl font-bold">${avgBet}</span>
          <span className="text-xs text-muted-foreground">Avg Bet</span>
        </div>
        <div className="flex flex-col">
          <span className="text-2xl font-bold">{avgConfidence}%</span>
          <span className="text-xs text-muted-foreground">Avg Confidence</span>
        </div>
        <div className="flex flex-col">
          <span className="text-2xl font-bold">{totalRounds}</span>
          <span className="text-xs text-muted-foreground">Rounds</span>
        </div>
      </div>
    </div>
  );
}
