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
import { Badge } from "@/components/ui/badge";
import { motion } from "motion/react";

export default function GameBoard() {
  useGameSocket("default");

  const phase = useGameStore((s) => s.state.phase);
  const players = useGameStore((s) => s.state.players);

  return (
    <div className="h-screen flex flex-col max-w-[90rem] mx-auto w-full">
      <WinSound />

      {/* ─── Header ─── */}
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between px-4 md:px-8 py-3 border-b border-border flex-shrink-0"
      >
        <h1 className="text-xl font-semibold tracking-tight text-foreground">
          Typesafe<span className="text-accent">21</span>
        </h1>
        {phase !== "idle" && (
          <Badge variant="secondary" className="text-xs font-mono tabular-nums capitalize">
            {phase.replace("_", " ")}
          </Badge>
        )}
      </motion.header>

      {/* ─── Main Content (scrollable) ─── */}
      <div className="flex-1 overflow-y-auto">
        {/* Mobile: single column */}
        <div className="flex flex-col md:hidden h-full">
          <div className="flex-1 overflow-y-auto p-4 gap-6 flex flex-col">
            <HeroScene />
            <section className="flex flex-col items-center gap-4">
              <DealerHand />
            </section>
            <div className="w-full h-px bg-border" />
            <section className="grid grid-cols-1 gap-4 w-full">
              {players.map((_p, i) => (
                <PlayerHand key={i} playerIndex={i} />
              ))}
            </section>
            <ChipScene />
            <div className="w-full h-px bg-border" />
            <LastAction />
            <Scoreboard />
            <ShoeIndicator />
            <StatsPanel />
            <CardTracker />
            <BalanceChart />
          </div>
        </div>

        {/* Desktop: two columns */}
        <div className="hidden md:flex gap-6 p-6 lg:p-8">
          {/* ─── Left Column: Game ─── */}
          <div className="flex-1 flex flex-col gap-6 min-w-0">
            <HeroScene />

            {/* Dealer */}
            <section className="flex flex-col items-center gap-4">
              <DealerHand />
            </section>

            {/* Divider */}
            <div className="w-full h-px bg-border" />

            {/* Players — equal widths */}
            <section className="grid grid-cols-3 gap-4 w-full">
              {players.map((_p, i) => (
                <PlayerHand key={i} playerIndex={i} />
              ))}
            </section>

            {/* Chip Stacks */}
            <ChipScene />

            {/* Divider */}
            <div className="w-full h-px bg-border" />

            {/* Scoreboard */}
            <Scoreboard />

            {/* Balance Chart */}
            <BalanceChart />
          </div>

          {/* ─── Right Column: Stats ─── */}
          <div className="w-72 xl:w-80 flex flex-col gap-4 flex-shrink-0">
            <LastAction />
            <ShoeIndicator />
            <StatsPanel />
            <CardTracker />
          </div>
        </div>
      </div>

      {/* ─── Controls (always visible) ─── */}
      <div className="flex-shrink-0 border-t border-border">
        <GameControls />
      </div>
    </div>
  );
}
