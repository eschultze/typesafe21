"use client";

import { useGameStore } from "@/stores/gameStore";

function StatsCard({ label, betHistory, confidenceHistory }: { label: string; betHistory: number[]; confidenceHistory: number[] }) {
  const avgBet =
    betHistory.length > 0
      ? Math.round(betHistory.reduce((a, b) => a + b, 0) / betHistory.length)
      : 0;

  const avgConfidence =
    confidenceHistory.length > 0
      ? (
          confidenceHistory.reduce((a, b) => a + b, 0) /
          confidenceHistory.length *
          100
        ).toFixed(1)
      : "0.0";

  const totalRounds = betHistory.length;

  return (
    <div className="flex flex-col p-3 rounded-[10px] bg-card border border-border">
      <span className="text-xs text-muted-foreground mb-2">{label}</span>
      <div className="flex items-center gap-6 text-center">
        <div className="flex flex-col">
          <span className="text-lg font-bold tabular-nums">${avgBet}</span>
          <span className="text-[10px] text-muted-foreground">Avg Bet</span>
        </div>
        <div className="flex flex-col">
          <span className="text-lg font-bold tabular-nums">{avgConfidence}%</span>
          <span className="text-[10px] text-muted-foreground">Confidence</span>
        </div>
        <div className="flex flex-col">
          <span className="text-lg font-bold tabular-nums">{totalRounds}</span>
          <span className="text-[10px] text-muted-foreground">Rounds</span>
        </div>
      </div>
    </div>
  );
}

export function StatsPanel() {
  const jevBetHistory = useGameStore((s) => s.jev_bet_history);
  const jevConfidenceHistory = useGameStore((s) => s.jev_confidence_history);
  const layaBetHistory = useGameStore((s) => s.laya_bet_history);
  const layaConfidenceHistory = useGameStore((s) => s.laya_confidence_history);

  return (
    <div className="flex flex-col gap-2 w-full">
      <StatsCard label="Jev" betHistory={jevBetHistory} confidenceHistory={jevConfidenceHistory} />
      <StatsCard label="Laya" betHistory={layaBetHistory} confidenceHistory={layaConfidenceHistory} />
    </div>
  );
}
