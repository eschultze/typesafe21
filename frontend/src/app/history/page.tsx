"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

interface Session {
  id: number;
  started_at: string;
  total_rounds: number;
  is_complete: number;
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
    <main className="min-h-screen p-8 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">
        <Link href="/game" className="text-green-500 hover:underline">
          ← Game
        </Link>{" "}
        | Session History
      </h1>

      {loading && (
        <p className="text-muted-foreground">Loading sessions...</p>
      )}

      {error && (
        <p className="text-red-400 mb-4">Error: {error}</p>
      )}

      {!loading && !error && sessions.length === 0 && (
        <p className="text-muted-foreground">No completed sessions yet. Play some rounds and click "End Session" to save your progress.</p>
      )}

      <div className="flex flex-col gap-3">
        {sessions.map((s) => (
          <div
            key={s.id}
            className="p-4 rounded-lg bg-white/5 border border-white/10 flex justify-between items-center"
          >
            <div>
              <span className="font-mono text-sm">Session #{s.id}</span>
              <span className="text-muted-foreground text-sm ml-3">
                {new Date(s.started_at).toLocaleDateString()}
              </span>
            </div>
            <span className="text-sm">{s.total_rounds} rounds</span>
          </div>
        ))}
      </div>
    </main>
  );
}
