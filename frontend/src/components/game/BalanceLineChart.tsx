"use client";

import { useGameStore } from "@/stores/gameStore";

interface BalanceLineChartProps {
  playerIndex: number;
}

export function BalanceLineChart({ playerIndex }: BalanceLineChartProps) {
  const player = useGameStore((s) => s.state.players[playerIndex]);

  if (!player || player.balance_history.length < 2) return null;

  const history = player.balance_history;
  const w = 200;
  const h = 40;
  const pad = 4;

  const min = Math.min(...history);
  const max = Math.max(...history);
  const range = max - min || 1;

  const points = history.map((v, i) => {
    const x = pad + (i / (history.length - 1)) * (w - pad * 2);
    const y = h - pad - ((v - min) / range) * (h - pad * 2);
    return `${x},${y}`;
  });

  const profit = history[history.length - 1] >= (history[0] ?? 100);
  const color = profit ? "var(--color-profit)" : "var(--color-loss)";
  const filterId = `balance-glow-${playerIndex}`;

  return (
    <svg
      viewBox={`0 0 ${w} ${h}`}
      className="w-full h-8 pointer-events-none"
      preserveAspectRatio="none"
      aria-hidden
    >
      <defs>
        <filter id={filterId}>
          <feGaussianBlur stdDeviation="2" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      <polyline
        points={points.join(" ")}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity="0.25"
        filter={`url(#${filterId})`}
      />
    </svg>
  );
}
