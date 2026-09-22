"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "motion/react";

interface PlayerRound {
  player_index: number;
  player_name: string;
  result: "win" | "lose" | "push" | null;
  bet: number;
  confidence: number;
  decision: string;
  balance_after: number;
}

interface Round {
  id: number;
  session_id: number;
  round_number: number;
  dealer_final_value: number;
  created_at: string;
  players: PlayerRound[];
}

interface PlayerStats {
  wins: number;
  losses: number;
  pushes: number;
  avg_confidence: number;
  total_rounds: number;
}

interface SessionData {
  stats: {
    players: Record<string, PlayerStats>;
    total_rounds: number;
  };
  rounds: Round[];
}

const resultColors: Record<string, string> = {
  win: "var(--color-profit)",
  lose: "var(--color-loss)",
  push: "var(--chart-4)",
};

const decisionColors: Record<string, string> = {
  hit: "var(--chart-2)",
  stand: "var(--color-profit)",
  double: "var(--chart-1)",
  split: "var(--chart-5)",
  "": "var(--muted)",
};

const decisionLabels: Record<string, string> = {
  hit: "Hit",
  stand: "Stand",
  double: "Double",
  split: "Split",
  "": "—",
};

export default function SessionDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const [data, setData] = useState<SessionData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string>("");

  useEffect(() => {
    params.then((p) => setSessionId(p.id));
  }, [params]);

  useEffect(() => {
    if (!sessionId) return;
    fetch(`/api/history/${sessionId}`)
      .then((r) => {
        if (!r.ok) throw new Error(`Failed to load session (${r.status})`);
        return r.json();
      })
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [sessionId]);

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col">
        <nav className="w-full border-b-2 border-border px-[var(--space-lg)] py-3 flex items-center justify-between">
          <span className="font-bold text-sm tracking-[0.16em] uppercase text-foreground">
            Typesafe 21
          </span>
          <div className="flex items-center gap-6 text-sm text-muted-foreground">
            <Link href="/history" className="hover:text-foreground transition-colors">
              History
            </Link>
            <Link href="/game" className="hover:text-foreground transition-colors">
              Play
            </Link>
          </div>
        </nav>
        <main className="flex-1 px-[var(--space-lg)] md:px-[var(--space-2xl)] py-[var(--space-2xl)] max-w-[76rem] mx-auto w-full">
          <div className="flex flex-col gap-4 max-w-3xl">
            <div className="h-8 w-48 rounded bg-muted animate-pulse" />
            <div className="h-40 rounded-[10px] bg-card border border-border animate-pulse" />
            <div className="h-48 rounded-[10px] bg-card border border-border animate-pulse" />
            <div className="h-48 rounded-[10px] bg-card border border-border animate-pulse" />
          </div>
        </main>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen flex flex-col">
        <nav className="w-full border-b-2 border-border px-[var(--space-lg)] py-3 flex items-center justify-between">
          <span className="font-bold text-sm tracking-[0.16em] uppercase text-foreground">
            Typesafe 21
          </span>
          <div className="flex items-center gap-6 text-sm text-muted-foreground">
            <Link href="/history" className="hover:text-foreground transition-colors">
              History
            </Link>
            <Link href="/game" className="hover:text-foreground transition-colors">
              Play
            </Link>
          </div>
        </nav>
        <main className="flex-1 px-[var(--space-lg)] md:px-[var(--space-2xl)] py-[var(--space-2xl)] max-w-[76rem] mx-auto w-full">
          <p className="text-[var(--color-destructive)]">Error: {error || "Session not found"}</p>
        </main>
      </div>
    );
  }

  const recentRounds = data.rounds.slice(-10);
  const playerNames = Object.keys(data.stats.players);

  return (
    <div className="min-h-screen flex flex-col">
      {/* ─── Nav ─── */}
      <nav className="w-full border-b-2 border-border px-[var(--space-lg)] py-3 flex items-center justify-between">
        <span className="font-bold text-sm tracking-[0.16em] uppercase text-foreground">
          Typesafe 21
        </span>
        <div className="flex items-center gap-6 text-sm text-muted-foreground">
          <Link href="/history" className="text-foreground font-medium hover:text-accent transition-colors">
            History
          </Link>
          <Link href="/game" className="hover:text-foreground transition-colors">
            Play
          </Link>
        </div>
      </nav>

      {/* ─── Content ─── */}
      <main className="flex-1 px-[var(--space-lg)] md:px-[var(--space-2xl)] py-[var(--space-2xl)] max-w-[76rem] mx-auto w-full">
        <div className="flex flex-col gap-6 max-w-3xl">
          {/* Header */}
          <div className="flex items-center gap-4">
            <Link
              href="/history"
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              ← Back
            </Link>
            <h1 className="text-[var(--text-display-s)] font-light tracking-[var(--tracking-tight)] text-foreground">
              Session #{sessionId}
            </h1>
            <span className="text-sm text-muted-foreground">
              {data.stats.total_rounds} rounds
            </span>
          </div>

          {/* ─── Player Stats Summary ─── */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {playerNames.map((name) => {
              const s = data.stats.players[name];
              const winRate = s.total_rounds > 0
                ? ((s.wins / s.total_rounds) * 100).toFixed(0)
                : "0";
              return (
                <div
                  key={name}
                  className="flex flex-col items-center p-3 rounded-[10px] bg-card border border-border"
                >
                  <span className="text-xs text-muted-foreground mb-1">{name}</span>
                  <span className="text-xl font-bold tabular-nums">
                    {s.wins}W / {s.losses}L / {s.pushes}P
                  </span>
                  <span className="text-xs text-muted-foreground tabular-nums">
                    {winRate}% win rate
                  </span>
                </div>
              );
            })}
          </div>

          {/* ─── Win/Lose Chart (last 10 rounds) ─── */}
          <div className="flex flex-col p-4 rounded-[10px] bg-card border border-border">
            <span className="text-xs text-muted-foreground mb-3">
              Win / Lose — Last {recentRounds.length} Rounds
            </span>
            <div className="flex gap-1 items-end h-32">
              {recentRounds.map((round) => {
                const jevResult = round.players.find(
                  (p) => p.player_name === "Jev (AI)"
                );
                const result = jevResult?.result || "push";
                return (
                  <div
                    key={round.id}
                    className="flex-1 flex flex-col items-center gap-1"
                  >
                    <motion.div
                      className="w-full rounded-t"
                      initial={{ height: 0 }}
                      animate={{ height: result === "win" ? "100%" : result === "lose" ? "60%" : "30%" }}
                      transition={{ type: "spring", stiffness: 200, damping: 20 }}
                      style={{
                        backgroundColor: resultColors[result] || resultColors.push,
                        minHeight: "4px",
                      }}
                    />
                    <span className="text-[9px] text-muted-foreground tabular-nums">
                      R{round.round_number}
                    </span>
                  </div>
                );
              })}
              {recentRounds.length === 0 && (
                <span className="text-xs text-muted-foreground">No rounds played</span>
              )}
            </div>
            <div className="flex gap-4 mt-3 text-[10px] text-muted-foreground">
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-sm" style={{ backgroundColor: resultColors.win }} />
                Win
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-sm" style={{ backgroundColor: resultColors.lose }} />
                Lose
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-sm" style={{ backgroundColor: resultColors.push }} />
                Push
              </span>
            </div>
          </div>

          {/* ─── AI Decisions Chart (last 10 rounds) ─── */}
          <div className="flex flex-col p-4 rounded-[10px] bg-card border border-border">
            <span className="text-xs text-muted-foreground mb-3">
              AI Decisions — Last {recentRounds.length} Rounds
            </span>
            <div className="flex gap-1 items-end h-32">
              {recentRounds.map((round) => {
                const jevResult = round.players.find(
                  (p) => p.player_name === "Jev (AI)"
                );
                const decision = jevResult?.decision || "";
                return (
                  <div
                    key={round.id}
                    className="flex-1 flex flex-col items-center gap-1"
                  >
                    <motion.div
                      className="w-full rounded-t"
                      initial={{ height: 0 }}
                      animate={{ height: decision ? "100%" : "10%" }}
                      transition={{ type: "spring", stiffness: 200, damping: 20 }}
                      style={{
                        backgroundColor: decisionColors[decision] || decisionColors[""],
                        minHeight: "4px",
                      }}
                    />
                    <span className="text-[9px] text-muted-foreground tabular-nums">
                      R{round.round_number}
                    </span>
                  </div>
                );
              })}
              {recentRounds.length === 0 && (
                <span className="text-xs text-muted-foreground">No rounds played</span>
              )}
            </div>
            <div className="flex flex-wrap gap-4 mt-3 text-[10px] text-muted-foreground">
              {Object.entries(decisionLabels).filter(([k]) => k !== "").map(([key, label]) => (
                <span key={key} className="flex items-center gap-1">
                  <span
                    className="w-2 h-2 rounded-sm"
                    style={{ backgroundColor: decisionColors[key] }}
                  />
                  {label}
                </span>
              ))}
            </div>
          </div>

          {/* ─── Round-by-Round Detail ─── */}
          <div className="flex flex-col gap-2">
            <span className="text-xs text-muted-foreground">Round Details</span>
            {data.rounds.map((round) => (
              <div
                key={round.id}
                className="p-3 rounded-[10px] bg-card border border-border"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-mono text-foreground">
                    Round {round.round_number}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    Dealer: {round.dealer_final_value}
                  </span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {round.players.map((p) => (
                    <span
                      key={p.player_index}
                      className="text-xs px-2 py-0.5 rounded-full border tabular-nums"
                      style={{
                        borderColor: resultColors[p.result || "push"],
                        color: resultColors[p.result || "push"],
                      }}
                    >
                      {p.player_name}: {p.result?.toUpperCase()}
                      {p.decision ? ` (${p.decision})` : ""}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
