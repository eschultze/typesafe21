"use client";

import { motion } from "motion/react";
import { useGameStore } from "@/stores/gameStore";

function ChartLine({ history, label }: { history: number[]; label: string }) {
  if (history.length < 2) return null;

  const width = 200;
  const height = 60;
  const padding = 4;

  const minVal = history.length > 0 ? Math.min(...history.slice(-500), 50) : 0;
  const maxVal = history.length > 0 ? Math.max(...history.slice(-500), 100) : 100;
  const range = maxVal - minVal || 1;

  const points = history.map((val, i) => {
    const x = padding + (i / Math.max(history.length - 1, 1)) * (width - padding * 2);
    const y = padding + (1 - (val - minVal) / range) * (height - padding * 2);
    return `${x},${y}`;
  });

  const pathD = `M ${points.join(" L ")}`;
  const areaD = `${pathD} L ${width - padding},${height - padding} L ${padding},${height - padding} Z`;

  const startingBalance = history[0] ?? 100;
  const currentBalance = history[history.length - 1];
  const profit = currentBalance - startingBalance;

  const strokeColor = profit >= 0 ? "var(--color-profit)" : "var(--color-loss)";

  return (
    <div className="flex flex-col items-center p-3 rounded-[10px] bg-card border border-border">
      <span className="text-xs text-muted-foreground mb-1">{label}</span>
      <svg width={width} height={height} className="overflow-visible">
        <defs>
          <linearGradient id={`chartGrad-${label}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={strokeColor} stopOpacity="0.3" />
            <stop offset="100%" stopColor={strokeColor} stopOpacity="0" />
          </linearGradient>
        </defs>
        <path d={areaD} fill={`url(#chartGrad-${label})`} />
        <motion.path
          d={pathD}
          fill="none"
          stroke={strokeColor}
          strokeWidth="2"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
        />
        {/* Baseline at starting balance */}
        <line
          x1={padding}
          y1={padding + (1 - (startingBalance - minVal) / range) * (height - padding * 2)}
          x2={width - padding}
          y2={padding + (1 - (startingBalance - minVal) / range) * (height - padding * 2)}
          stroke="var(--color-muted-foreground)"
          strokeOpacity="0.3"
          strokeDasharray="4 4"
        />
      </svg>
    </div>
  );
}

export function BalanceChart() {
  const players = useGameStore((s) => s.state.players);

  if (players.length === 0) return null;

  const jevPlayer = players.find((p) => p.name === "Jev (AI)");
  const layaPlayer = players.find((p) => p.name === "Laya (AI)");

  return (
    <div className="grid grid-cols-2 gap-2 w-full">
      {jevPlayer && jevPlayer.balance_history.length >= 2 && (
        <ChartLine history={jevPlayer.balance_history} label="Jev Balance" />
      )}
      {layaPlayer && layaPlayer.balance_history.length >= 2 && (
        <ChartLine history={layaPlayer.balance_history} label="Laya Balance" />
      )}
    </div>
  );
}
