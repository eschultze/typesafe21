"use client";

import { motion } from "motion/react";
import { useGameStore } from "@/stores/gameStore";

export function BalanceChart() {
  const players = useGameStore((s) => s.state.players);

  if (players.length === 0) return null;

  const aiPlayer = players.find((p) => p.name === "You");
  if (!aiPlayer || aiPlayer.balance_history.length < 2) return null;

  const history = aiPlayer.balance_history;
  const maxVal = Math.max(...history, 100);
  const minVal = Math.min(...history, 50);
  const range = maxVal - minVal || 1;

  const width = 200;
  const height = 60;
  const padding = 4;

  const points = history.map((val, i) => {
    const x = padding + (i / Math.max(history.length - 1, 1)) * (width - padding * 2);
    const y = padding + (1 - (val - minVal) / range) * (height - padding * 2);
    return `${x},${y}`;
  });

  const pathD = `M ${points.join(" L ")}`;
  const areaD = `${pathD} L ${width - padding},${height - padding} L ${padding},${height - padding} Z`;

  const startingBalance = history[0] ?? 100;
  const profit = aiPlayer.balance - startingBalance;

  const strokeColor = profit >= 0 ? "var(--color-profit)" : "var(--color-loss)";

  return (
    <div className="flex flex-col items-center p-3 rounded-[10px] bg-card border border-border">
      <span className="text-xs text-muted-foreground mb-1">AI Balance</span>
      <svg width={width} height={height} className="overflow-visible">
        <defs>
          <linearGradient id="chartGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={strokeColor} stopOpacity="0.3" />
            <stop offset="100%" stopColor={strokeColor} stopOpacity="0" />
          </linearGradient>
        </defs>
        <path d={areaD} fill="url(#chartGrad)" />
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
