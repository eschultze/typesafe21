"use client";

import { useState } from "react";
import { useGameStore } from "@/stores/gameStore";
import { usePolledJson } from "@/hooks/usePolledJson";

const JEV = "Jev (AI)";
const LAYA = "Laya (AI)";

interface PlayerMetrics {
  n: number;
  wagered: number;
  profit: number;
  edge: number;
  wins: number;
  losses: number;
  pushes: number;
  win_rate: number;
  avg_bet: number;
  max_bet: number;
  avg_confidence: number;
  calib_gap: number | null;
  brier: number | null;
  p50_latency: number;
  p95_latency: number;
  tokens_per_decision: number;
  tokens_total: number;
  decisions_per_round: number;
  max_drawdown: number;
  volatility: number;
  ret_vol: number;
}

interface TCStats {
  n: number;
  avg_bet: number;
  ev: number;
}

interface BenchmarkData {
  scope: string;
  session_id: number | null;
  total_rounds: number;
  sessions: number;
  players: Record<string, PlayerMetrics>;
  head_to_head: {
    n: number;
    mean: number;
    ci: number;
    jev_wins: number;
    laya_wins: number;
    ties: number;
  };
  by_true_count: Array<{ label: string; jev: TCStats; laya: TCStats }>;
}

const EMPTY: PlayerMetrics = {
  n: 0,
  wagered: 0,
  profit: 0,
  edge: 0,
  wins: 0,
  losses: 0,
  pushes: 0,
  win_rate: 0,
  avg_bet: 0,
  max_bet: 0,
  avg_confidence: 0,
  calib_gap: null,
  brier: null,
  p50_latency: 0,
  p95_latency: 0,
  tokens_per_decision: 0,
  tokens_total: 0,
  decisions_per_round: 0,
  max_drawdown: 0,
  volatility: 0,
  ret_vol: 0,
};

const money = (v: number) => `${v >= 0 ? "+" : "−"}$${Math.abs(Math.round(v))}`;
const pct1 = (v: number) => `${v.toFixed(1)}%`;

function Row({
  label,
  jev,
  laya,
  higherIsBetter = true,
  jevRaw,
  layaRaw,
}: {
  label: string;
  jev: string;
  laya: string;
  higherIsBetter?: boolean;
  jevRaw?: number;
  layaRaw?: number;
}) {
  let jevTone = "";
  let layaTone = "";
  if (typeof jevRaw === "number" && typeof layaRaw === "number" && jevRaw !== layaRaw) {
    const jevBetter = higherIsBetter ? jevRaw > layaRaw : jevRaw < layaRaw;
    jevTone = jevBetter ? "text-[var(--color-profit)]" : "text-muted-foreground";
    layaTone = jevBetter ? "text-muted-foreground" : "text-[var(--color-profit)]";
  }
  return (
    <div className="grid grid-cols-[1fr_auto_auto] items-baseline gap-x-2 py-0.5">
      <span className="text-[10px] text-muted-foreground truncate">{label}</span>
      <span className={`text-[11px] font-semibold tabular-nums text-right ${jevTone}`}>{jev}</span>
      <span className={`text-[11px] font-semibold tabular-nums text-right ${layaTone}`}>{laya}</span>
    </div>
  );
}

export function BenchmarkPanel() {
  const sessionId = useGameStore((s) => s.state.session_id);
  const [scope, setScope] = useState<"session" | "all_time">("session");
  const [tab, setTab] = useState<"score" | "bet" | "risk">("score");

  const url =
    scope === "session"
      ? sessionId
        ? `/api/benchmark?session_id=${sessionId}`
        : null
      : "/api/benchmark";
  const data = usePolledJson<BenchmarkData>(url, 4000);

  const jev = data?.players[JEV] ?? EMPTY;
  const laya = data?.players[LAYA] ?? EMPTY;
  const h2h =
    data?.head_to_head ?? { n: 0, mean: 0, ci: 0, jev_wins: 0, laya_wins: 0, ties: 0 };
  const byTrueCount = data?.by_true_count ?? [];
  const totalRounds = data?.total_rounds ?? 0;
  const sessionCount = data?.sessions ?? 0;
  const hasData = jev.n > 0 || laya.n > 0;
  const hasLatency = jev.p50_latency > 0 || laya.p50_latency > 0;
  const leader = jev.profit === laya.profit ? "tied" : jev.profit > laya.profit ? "Jev" : "Laya";

  return (
    <div className="flex flex-col p-3 rounded-[10px] bg-card border border-border">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-muted-foreground">Benchmark</span>
        <span className="text-[10px] text-muted-foreground tabular-nums">
          {totalRounds} rounds
          {scope === "all_time" && sessionCount > 0 ? ` · ${sessionCount} sessions` : ""}
        </span>
      </div>

      {/* Scope toggle */}
      <div className="flex gap-1 p-0.5 mb-2 rounded-lg bg-muted/40">
        {(["session", "all_time"] as const).map((s) => (
          <button
            key={s}
            onClick={() => setScope(s)}
            className={`flex-1 text-[10px] py-1 rounded-md transition-colors ${
              scope === s
                ? "bg-background text-foreground font-semibold shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {s === "session" ? "This session" : "All time"}
          </button>
        ))}
      </div>

      {!hasData ? (
        <span className="text-[10px] text-muted-foreground py-2">
          No rounds recorded {scope === "session" ? "in this session" : "yet"}.
        </span>
      ) : (
        <>
          <div className="grid grid-cols-[1fr_auto_auto] items-baseline gap-x-2 pb-1 mb-1 border-b border-border">
            <span className="text-[10px] uppercase tracking-wider text-muted-foreground/70">Metric</span>
            <span className="text-[11px] font-semibold text-accent text-right">Jev</span>
            <span className="text-[11px] font-semibold text-accent text-right">Laya</span>
          </div>

          {tab === "score" && (
            <div className="flex flex-col">
              <Row label="Edge (ROI)" jev={`${jev.edge >= 0 ? "+" : ""}${jev.edge.toFixed(1)}%`} laya={`${laya.edge >= 0 ? "+" : ""}${laya.edge.toFixed(1)}%`} jevRaw={jev.edge} layaRaw={laya.edge} />
              <Row label="Net profit" jev={money(jev.profit)} laya={money(laya.profit)} jevRaw={jev.profit} layaRaw={laya.profit} />
              <Row label="Win rate" jev={pct1(jev.win_rate)} laya={pct1(laya.win_rate)} jevRaw={jev.win_rate} layaRaw={laya.win_rate} />
              <Row label="W / P / L" jev={`${jev.wins}/${jev.pushes}/${jev.losses}`} laya={`${laya.wins}/${laya.pushes}/${laya.losses}`} />
              <Row label="Avg bet" jev={`$${Math.round(jev.avg_bet)}`} laya={`$${Math.round(laya.avg_bet)}`} />
              <Row label="Confidence" jev={pct1(jev.avg_confidence)} laya={pct1(laya.avg_confidence)} />
              <Row
                label="Calibration"
                jev={jev.calib_gap === null ? "—" : `${jev.calib_gap.toFixed(0)} pts`}
                laya={laya.calib_gap === null ? "—" : `${laya.calib_gap.toFixed(0)} pts`}
                higherIsBetter={false}
                jevRaw={jev.calib_gap ?? undefined}
                layaRaw={laya.calib_gap ?? undefined}
              />
              {hasLatency && (
                <Row
                  label="Latency p50/p95"
                  jev={jev.p50_latency > 0 ? `${Math.round(jev.p50_latency)}/${Math.round(jev.p95_latency)}ms` : "—"}
                  laya={laya.p50_latency > 0 ? `${Math.round(laya.p50_latency)}/${Math.round(laya.p95_latency)}ms` : "—"}
                />
              )}
              {jev.tokens_per_decision > 0 && (
                <Row label="Tokens / dec" jev={Math.round(jev.tokens_per_decision).toString()} laya="0 (local)" />
              )}
              {jev.decisions_per_round > 0 && (
                <Row
                  label="AI calls / round"
                  jev={jev.decisions_per_round.toFixed(1)}
                  laya={laya.decisions_per_round.toFixed(1)}
                  higherIsBetter={false}
                  jevRaw={jev.decisions_per_round}
                  layaRaw={laya.decisions_per_round}
                />
              )}

              <div className="mt-2 pt-2 border-t border-border text-[10px] text-muted-foreground leading-relaxed">
                <div className="flex items-center justify-between">
                  <span>Head-to-head</span>
                  <span className="tabular-nums text-foreground font-semibold">
                    {h2h.jev_wins}–{h2h.ties}–{h2h.laya_wins}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Per-round diff</span>
                  <span className="tabular-nums text-foreground font-semibold">
                    {money(h2h.mean)} ± ${h2h.ci.toFixed(1)}
                  </span>
                </div>
                <div className="text-muted-foreground/60 mt-0.5">
                  {h2h.n === 0
                    ? "No head-to-head rounds yet."
                    : leader === "tied"
                    ? "Dead even."
                    : `${leader} leads. Diff is ${h2h.ci > Math.abs(h2h.mean) ? "not yet " : ""}significant at 95%.`}
                </div>
              </div>
            </div>
          )}

          {tab === "bet" && (
            <div className="flex flex-col">
              <Row label="Avg / max bet" jev={`$${Math.round(jev.avg_bet)} / $${jev.max_bet}`} laya={`$${Math.round(laya.avg_bet)} / $${laya.max_bet}`} />
              <div className="mt-2 pt-2 border-t border-border">
                <div className="grid grid-cols-[1fr_auto_auto] gap-x-2 pb-1">
                  <span className="text-[10px] text-muted-foreground/70">True count</span>
                  <span className="text-[10px] text-muted-foreground/70 text-right">Jev bet · EV</span>
                  <span className="text-[10px] text-muted-foreground/70 text-right">Laya bet · EV</span>
                </div>
                {byTrueCount.map((b) => (
                  <div key={b.label} className="grid grid-cols-[1fr_auto_auto] gap-x-2 py-0.5">
                    <span className="text-[10px] text-muted-foreground">{b.label}</span>
                    <span className="text-[11px] tabular-nums text-right text-foreground">
                      {b.jev.n > 0 ? `$${Math.round(b.jev.avg_bet)}` : "—"}{" "}
                      {b.jev.n > 0 && (
                        <span className={b.jev.ev >= 0 ? "text-[var(--color-profit)]" : "text-[var(--color-loss)]"}>{money(b.jev.ev)}</span>
                      )}
                    </span>
                    <span className="text-[11px] tabular-nums text-right text-foreground">
                      {b.laya.n > 0 ? `$${Math.round(b.laya.avg_bet)}` : "—"}{" "}
                      {b.laya.n > 0 && (
                        <span className={b.laya.ev >= 0 ? "text-[var(--color-profit)]" : "text-[var(--color-loss)]"}>{money(b.laya.ev)}</span>
                      )}
                    </span>
                  </div>
                ))}
                {byTrueCount.every((b) => b.jev.n === 0 && b.laya.n === 0) && (
                  <span className="text-[10px] text-muted-foreground/60">
                    Count data starts recording with new rounds.
                  </span>
                )}
              </div>
            </div>
          )}

          {tab === "risk" && (
            <div className="flex flex-col">
              <Row label="Max drawdown" jev={`−$${Math.round(jev.max_drawdown)}`} laya={`−$${Math.round(laya.max_drawdown)}`} higherIsBetter={false} jevRaw={jev.max_drawdown} layaRaw={laya.max_drawdown} />
              <Row label="Volatility / round" jev={`$${jev.volatility.toFixed(1)}`} laya={`$${laya.volatility.toFixed(1)}`} higherIsBetter={false} jevRaw={jev.volatility} layaRaw={laya.volatility} />
              <Row label="Return / risk" jev={jev.ret_vol.toFixed(2)} laya={laya.ret_vol.toFixed(2)} jevRaw={jev.ret_vol} layaRaw={laya.ret_vol} />
              <Row label="Brier score" jev={jev.brier === null ? "—" : jev.brier.toFixed(3)} laya={laya.brier === null ? "—" : laya.brier.toFixed(3)} higherIsBetter={false} jevRaw={jev.brier ?? undefined} layaRaw={laya.brier ?? undefined} />
            </div>
          )}

          <div className="flex gap-1 mt-3 pt-2 border-t border-border">
            {(["score", "bet", "risk"] as const).map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`flex-1 text-[10px] py-1 rounded-md transition-colors ${
                  tab === t
                    ? "bg-accent/15 text-accent font-semibold"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {t === "score" ? "Scorecard" : t === "bet" ? "Betting" : "Risk"}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
