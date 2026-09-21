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
import { motion } from "motion/react";

export default function GameBoard() {
  useGameSocket("default");

  const phase = useGameStore((s) => s.state.phase);
  const players = useGameStore((s) => s.state.players);

  return (
    <main className="min-h-screen flex flex-col items-center p-4 md:p-8 gap-6">
      <WinSound />
      <motion.h1
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-3xl font-bold tracking-tight"
      >
        TypeSafe<span className="text-green-500">21</span>
      </motion.h1>

      <HeroScene />

      <div className="w-full max-w-4xl flex flex-col items-center gap-6">
        {/* Dealer */}
        <DealerHand />

        {/* Table divider */}
        <div className="w-full h-px bg-gradient-to-r from-transparent via-white/20 to-transparent" />

        {/* Players */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 w-full">
          {players.map((_, i) => (
            <PlayerHand key={i} playerIndex={i} />
          ))}
        </div>

        {/* Table divider */}
        <div className="w-full h-px bg-gradient-to-r from-transparent via-white/20 to-transparent" />

        {/* Last action */}
        <LastAction />

        {/* Scoreboard */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 w-full">
          <Scoreboard />
        </div>

        {/* Shoe + Balance + Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 w-full">
          <ShoeIndicator />
          <BalanceChart />
          <StatsPanel />
        </div>

        {/* Card tracker */}
        <div className="w-full">
          <CardTracker />
        </div>

        {/* Controls */}
        <GameControls />

        {/* Phase indicator */}
        {phase !== "idle" && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-sm text-muted-foreground"
          >
            Phase: <span className="font-mono text-foreground">{phase}</span>
          </motion.div>
        )}
      </div>
    </main>
  );
}
