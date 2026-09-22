"use client";

import { useEffect, useState } from "react";

interface SingleTurnEntry {
  session_id: number;
  player_name: string;
  round_number: number;
  bet: number;
  result: string;
  profit: number;
}

interface SessionEntry {
  session_id: number;
  player_name: string;
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
    <div className="flex flex-col gap-3 p-3 rounded-[10px] bg-card border border-border">
      <span className="text-xs text-muted-foreground">Leaderboard</span>

      {hasSingleTurn && (
        <div className="flex flex-col">
          <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium mb-2">
            Best Single Turn
          </span>
          <div className="flex flex-col gap-1.5">
            {data.single_turn.map((entry, i) => (
              <div
                key={`${entry.session_id}-${entry.round_number}-${i}`}
                className="flex items-center gap-1.5 text-xs"
              >
                <span className="text-muted-foreground/60 font-mono text-[10px] w-4 text-right shrink-0">
                  {i + 1}
                </span>
                <span className="text-foreground font-medium min-w-0 truncate">
                  {entry.player_name}
                </span>
                <span className="text-muted-foreground text-[10px] tabular-nums shrink-0 ml-auto">
                  S{entry.session_id} &middot; R{entry.round_number}
                </span>
                <span className="font-bold tabular-nums text-[var(--color-profit)] shrink-0">
                  +${entry.profit}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {hasSessions && (
        <div className="flex flex-col">
          <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium mb-2">
            Best Sessions
          </span>
          <div className="flex flex-col gap-1.5">
            {data.sessions.map((entry, i) => (
              <div
                key={`${entry.session_id}-${i}`}
                className="flex items-center gap-1.5 text-xs"
              >
                <span className="text-muted-foreground/60 font-mono text-[10px] w-4 text-right shrink-0">
                  {i + 1}
                </span>
                <span className="text-foreground font-medium min-w-0 truncate">
                  {entry.player_name}
                </span>
                <span className="text-muted-foreground text-[10px] tabular-nums shrink-0 ml-auto">
                  S{entry.session_id} &middot;{" "}
                  {entry.total_rounds === 1
                    ? "1 round"
                    : `${entry.total_rounds} rounds`}
                </span>
                <span
                  className={`font-bold tabular-nums shrink-0 ${
                    entry.profit >= 0
                      ? "text-[var(--color-profit)]"
                      : "text-[var(--color-loss)]"
                  }`}
                >
                  {entry.profit >= 0 ? "+" : ""}${entry.profit}{" "}
                  <span className="text-[10px] opacity-80">({entry.pct}%)</span>
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
