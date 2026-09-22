"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Nav } from "@/components/Nav";

interface Session {
  id: number;
  started_at: string;
  total_rounds: number;
  is_complete: number;
}

function SkeletonCard() {
  return (
    <div className="p-4 rounded-[10px] bg-card border border-border animate-pulse">
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="h-4 w-24 rounded bg-muted" />
          <div className="h-4 w-20 rounded bg-muted" />
        </div>
        <div className="h-4 w-16 rounded bg-muted" />
      </div>
    </div>
  );
}

export default function HistoryPage() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/history")
      .then((r) => {
        if (!r.ok) throw new Error(`Failed to load history (${r.status})`);
        return r.json();
      })
      .then(setSessions)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen flex flex-col">
      <Nav />

      {/* ─── Content ─── */}
      <main className="flex-1 px-[var(--space-lg)] md:px-[var(--space-2xl)] py-[var(--space-2xl)] max-w-[76rem] mx-auto w-full">
        <h1 className="text-3xl md:text-4xl font-light tracking-tight text-foreground mb-[var(--space-xl)]">
          Session History
        </h1>

        {loading && (
          <div className="flex flex-col gap-3 max-w-2xl">
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </div>
        )}

        {error && (
          <p className="text-[var(--color-destructive)] mb-4">Error: {error}</p>
        )}

        {!loading && !error && sessions.length === 0 && (
          <div className="flex flex-col gap-3 max-w-2xl">
            <p className="text-muted-foreground">
              No completed sessions yet. Play some rounds and click &quot;End Session&quot; to save your progress.
            </p>
            <Link
              href="/game"
              className="inline-flex items-center gap-2 text-foreground font-medium text-base hover:text-accent transition-colors group mt-4"
            >
              Start Playing
              <span className="group-hover:translate-x-1 transition-transform">&rarr;</span>
            </Link>
          </div>
        )}

        <div className="flex flex-col gap-3 max-w-2xl">
          {sessions.map((s) => (
            <Link
              key={s.id}
              href={`/history/${s.id}`}
              className="p-4 rounded-[10px] bg-card border border-border flex justify-between items-center cursor-pointer transition-all hover:border-accent/30 hover:bg-accent/5"
            >
              <div className="flex items-center gap-3">
                <span className="font-mono text-sm text-foreground">Session #{s.id}</span>
                <span className="text-muted-foreground text-sm">
                  {new Date(s.started_at).toLocaleDateString()}
                </span>
              </div>
              <span className="text-sm text-muted-foreground tabular-nums">
                {s.total_rounds} {s.total_rounds === 1 ? "round" : "rounds"}
              </span>
            </Link>
          ))}
        </div>
      </main>
    </div>
  );
}
