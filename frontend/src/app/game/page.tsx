"use client";

import { useGameSocket } from "@/hooks/useGameSocket";
import { useGameStore } from "@/stores/gameStore";
import { DealerHand } from "@/components/game/DealerHand";
import { PlayerHand } from "@/components/game/PlayerHand";
import { Scoreboard } from "@/components/game/Scoreboard";
import { ShoeIndicator } from "@/components/game/ShoeIndicator";
import { BalanceChart } from "@/components/game/BalanceChart";
import { GameControls } from "@/components/game/GameControls";
import { LastAction } from "@/components/game/LastAction";
import { HeroScene } from "@/components/game/HeroScene";
import { WinSound } from "@/components/game/WinSound";
import { StatsPanel } from "@/components/game/StatsPanel";
import { CardTracker } from "@/components/game/CardTracker";
import { ChipScene } from "@/components/game/ChipScene";
import { motion } from "motion/react";

export default function GameBoard() {
  useGameSocket("default");

  const phase = useGameStore((s) => s.state.phase);
  const players = useGameStore((s) => s.state.players);

  return (
    <main className="min-h-screen flex flex-col p-4 md:px-8 md:py-6 gap-6 max-w-[76rem] mx-auto w-full">
      <WinSound />

      {/* ─── Header ─── */}
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <h1 className="text-xl font-semibold tracking-tight text-foreground">
          Typesafe<span className="text-accent">21</span>
        </h1>
        {phase !== "idle" && (
          <span className="text-xs font-mono text-muted-foreground tabular-nums">
            {phase}
          </span>
        )}
      </motion.header>

      {/* ─── Hero Scene (shows on round 0) ─── */}
      <HeroScene />

      {/* ─── Dealer ─── */}
      <section className="flex flex-col items-center gap-4">
        <DealerHand />
      </section>

      {/* ─── Divider ─── */}
      <div className="w-full h-px bg-border" />

      {/* ─── Players — varied widths ─── */}
      <section className="grid grid-cols-1 md:grid-cols-[1.2fr_1fr_0.8fr] gap-4 w-full">
        {players.map((_p, i) => (
          <PlayerHand key={i} playerIndex={i} />
        ))}
      </section>

      {/* ─── Chip Stacks ─── */}
      <ChipScene />

      {/* ─── Divider ─── */}
      <div className="w-full h-px bg-border" />

      {/* ─── Last Action ─── */}
      <LastAction />

      {/* ─── Scoreboard ─── */}
      <Scoreboard />

      {/* ─── Stats Row — shoe + chart + stats ─── */}
      <section className="grid grid-cols-1 md:grid-cols-[1fr_1.5fr_1fr] gap-4 w-full">
        <ShoeIndicator />
        <BalanceChart />
        <StatsPanel />
      </section>

      {/* ─── Card Tracker ─── */}
      <CardTracker />

      {/* ─── Controls ─── */}
      <GameControls />
    </main>
  );
}
