"use client";

import { useEffect, useState } from "react";

interface SingleTurnEntry {
  session_id: number;
  round_number: number;
  bet: number;
  result: string;
  profit: number;
}

interface SessionEntry {
  session_id: number;
  final_balance: number;
  profit: number;
  pct: number;
  total_rounds: number;
}

interface LeaderboardData {
  single_turn: SingleTurnEntry[];
  sessions: SessionEntry[];
}

export function Leaderboard() {
  const [data, setData] = useState<LeaderboardData | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let active = true;

    async function fetchLeaderboard() {
      try {
        const res = await fetch("/api/leaderboard");
        if (res.ok && active) {
          setData(await res.json());
        }
      } catch {
        if (active) setError(true);
      }
    }

    fetchLeaderboard();
    const interval = setInterval(fetchLeaderboard, 5000);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, []);

  if (error) return null;
  if (!data) return null;

  const hasSingleTurn = data.single_turn.length > 0;
  const hasSessions = data.sessions.length > 0;

  if (!hasSingleTurn && !hasSessions) return null;

  return (
    <div className="flex flex-col p-3 rounded-[10px] bg-card border border-border">
      <span className="text-xs text-muted-foreground mb-2">Leaderboard</span>

      {hasSingleTurn && (
        <div className="flex flex-col gap-1 mb-3">
          <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium">
            Best Single Turn
          </span>
          {data.single_turn.map((entry, i) => (
            <div
              key={`${entry.session_id}-${entry.round_number}`}
              className="flex items-center justify-between text-xs"
            >
              <span className="text-muted-foreground tabular-nums">
                #{i + 1} Session #{entry.session_id} Round {entry.round_number}
              </span>
              <span className="font-bold tabular-nums text-[var(--color-profit)]">
                +${entry.profit}
              </span>
            </div>
          ))}
        </div>
      )}

      {hasSessions && (
        <div className="flex flex-col gap-1">
          <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium">
            Best Sessions
          </span>
          {data.sessions.map((entry, i) => (
            <div
              key={entry.session_id}
              className="flex items-center justify-between text-xs"
            >
              <span className="text-muted-foreground tabular-nums">
                #{i + 1} Session #{entry.session_id}:{" "}
                {entry.total_rounds} {entry.total_rounds === 1 ? "round" : "rounds"}
              </span>
              <span
                className={`font-bold tabular-nums ${
                  entry.profit >= 0
                    ? "text-[var(--color-profit)]"
                    : "text-[var(--color-loss)]"
                }`}
              >
                {entry.profit >= 0 ? "+" : ""}${entry.profit} ({entry.pct}%)
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
