"use client";

import { motion, AnimatePresence } from "motion/react";
import { useGameStore } from "@/stores/gameStore";
import { PlayingCard } from "./PlayingCard";
import { Badge } from "@/components/ui/badge";

const DENOM_COLORS: Record<number, string> = {
  25: "#22c55e",
  10: "#3b82f6",
  5:  "#ef4444",
  1:  "#a855f7",
};
const CHIP_ORDER = [25, 10, 5, 1];
const MAX_CHIPS = 5;

function breakIntoChips(bet: number): number[] {
  const chips: number[] = [];
  let remaining = bet;
  for (const denom of CHIP_ORDER) {
    while (remaining >= denom && chips.length < MAX_CHIPS) {
      chips.push(denom);
      remaining -= denom;
    }
  }
  if (remaining > 0 && chips.length < MAX_CHIPS) chips.push(remaining);
  return chips;
}

function seededRandom(seed: number) {
  const x = Math.sin(seed * 9301 + 49297) * 49297;
  return x - Math.floor(x);
}

function InlineChips({ bet }: { bet: number }) {
  const animating = useGameStore((s) => s.chipsAnimating);
  const autoPlay = useGameStore((s) => s.state.auto_play);
  const chips = breakIntoChips(bet);
  const speed = autoPlay ? 2 : 1;
  const n = chips.length;

  if (n === 0) return null;

  const tilt = (i: number) => (seededRandom(chips[i] * 17 + i * 31) - 0.5) * 18;
  const wobbleX = (i: number) => (seededRandom(chips[i] * 23 + i * 47) - 0.5) * 8;

  return (
    <div className={`inline-chips-row inline-chips-${n}`}>
      <AnimatePresence mode="popLayout">
        {chips.map((denom, i) => (
          <motion.div
            key={`${denom}-${i}`}
            initial={animating ? { rotateY: 90, scale: 0 } : false}
            animate={{ rotateY: 0, scale: 1, rotate: tilt(i) }}
            transition={{
              type: "spring",
              stiffness: 260 * speed,
              damping: 18,
              delay: i * 0.07 * (1 / speed),
            }}
            className="inline-chip"
            style={{
              backgroundColor: DENOM_COLORS[denom] || "#888",
              marginLeft: `${wobbleX(i)}px`,
              marginRight: `${-wobbleX(i)}px`,
            } as React.CSSProperties}
          />
        ))}
      </AnimatePresence>
    </div>
  );
}

interface PlayerHandProps {
  playerIndex: number;
}

export function PlayerHand({ playerIndex }: PlayerHandProps) {
  const player = useGameStore((s) => s.state.players[playerIndex]);
  const isActive = useGameStore((s) => s.state.current_player === player?.name);
  const phase = useGameStore((s) => s.state.phase);

  if (!player) return null;

  const hand = player.hand;
  const isAI = player.name === "Jev (AI)" || player.name === "Laya (AI)";
  const cardCount = hand.cards.length;

  const cardSize = cardCount <= 2 ? "md" : "sm";

  return (
    <div
      className={`player-tile flex rounded-xl border transition-all duration-[var(--dur-short)] ${
        isActive
          ? "border-accent/50 bg-accent/5 shadow-[0_0_20px_var(--color-active-glow)]"
          : "border-border bg-card"
      }`}
    >
      {/* Main content (80%) */}
      <div className="flex-[4] flex flex-col items-center gap-2 p-3 min-w-0 relative">
        {isActive && isAI && phase === "player_turn" && (
          <div className="ai-thinking-overlay">
            <div className="ai-thinking-dots">
              <span /><span /><span />
            </div>
            <span className="ai-thinking-label">{player.name} thinking...</span>
          </div>
        )}

        <div className="flex items-center gap-2">
          <Badge
            variant={isAI ? "default" : "secondary"}
            className={isAI ? "bg-accent text-accent-foreground" : ""}
          >
            {player.name}
          </Badge>
          {hand.is_blackjack && (
            <Badge className="bg-yellow-500 text-black">BJ</Badge>
          )}
          {hand.is_bust && (
            <Badge variant="destructive">Bust</Badge>
          )}
          {!player.can_play && (
            <Badge variant="outline" className="text-muted-foreground border-muted-foreground/40">
              Out
            </Badge>
          )}
          <motion.span
            key={hand.value}
            initial={{ scale: 1.3 }}
            animate={{ scale: 1 }}
            transition={{ duration: 0.12, ease: [0.16, 1, 0.3, 1] }}
            className="text-lg font-bold tabular-nums"
          >
            {hand.value}
          </motion.span>
        </div>

        <div className="flex gap-1 justify-center flex-wrap">
          <AnimatePresence mode="popLayout">
            {hand.cards.map((card, i) => (
              <PlayingCard
                key={`${card.rank}-${card.suit}-${i}`}
                card={card}
                index={i}
                size={cardSize}
              />
            ))}
          </AnimatePresence>
        </div>

        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          <span>Balance: <span className={`font-bold tabular-nums ${player.balance >= 100 ? "text-[var(--color-profit)]" : "text-[var(--color-loss)]"}`}>${player.balance}</span></span>
          <span className="tabular-nums">{player.wins}W / {player.losses}L / {player.pushes}P</span>
        </div>

        {player.balance_history.length > 1 && (
          <div className="flex gap-1">
            {(() => {
              const h = player.balance_history;
              const start = Math.max(1, h.length - 5);
              const results: string[] = [];
              for (let i = start; i < h.length; i++) {
                if (h[i] > h[i - 1]) results.push("win");
                else if (h[i] < h[i - 1]) results.push("loss");
                else results.push("push");
              }
              return results.map((r, i) => (
                <div
                  key={start + i}
                  className={`w-2 h-2 rounded-full ${
                    r === "win"
                      ? "bg-[var(--color-profit)]"
                      : r === "loss"
                      ? "bg-[var(--color-loss)]"
                      : "bg-muted-foreground/40"
                  }`}
                />
              ));
            })()}
          </div>
        )}
      </div>

      {/* Chip side column (20%) */}
      {player.current_bet > 0 && (
        <div className="chip-side-col">
          <InlineChips bet={player.current_bet} />
          <span className="chip-bet-label">${player.current_bet}</span>
        </div>
      )}
    </div>
  );
}
