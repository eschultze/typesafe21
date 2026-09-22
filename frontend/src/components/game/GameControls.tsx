"use client";

import { useState, useRef, useEffect } from "react";
import { useGameStore } from "@/stores/gameStore";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export function GameControls() {
  const phase = useGameStore((s) => s.state.phase);
  const auto_play = useGameStore((s) => s.state.auto_play);
  const round_number = useGameStore((s) => s.state.round_number);
  const sendAction = useGameStore((s) => s.sendAction);
  const connected = useGameStore((s) => s.connected);
  const [confirmNewGame, setConfirmNewGame] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  const isIdle = phase === "idle";

  const handleNewGame = () => {
    if (!confirmNewGame) {
      setConfirmNewGame(true);
      timerRef.current = setTimeout(() => setConfirmNewGame(false), 3000);
      return;
    }
    if (timerRef.current) clearTimeout(timerRef.current);
    setConfirmNewGame(false);
    sendAction("new_game");
  };

  return (
    <div className="px-4 py-3 md:px-6 md:py-4">
      <div className="flex flex-col gap-3">
        <div className="flex items-center gap-2">
          <Badge variant={connected ? "default" : "destructive"}>
            {connected ? "Connected" : "Disconnected"}
          </Badge>
          {round_number > 0 && (
            <Badge variant="secondary" className="tabular-nums">Round {round_number}</Badge>
          )}
          {auto_play && (
            <Badge className="bg-accent text-accent-foreground">Auto-Playing</Badge>
          )}
        </div>

        <div className="flex flex-wrap gap-2">
          <Button
            onClick={handleNewGame}
            disabled={!connected}
            variant="outline"
            className={confirmNewGame ? "bg-[var(--color-destructive)] text-white border-[var(--color-destructive)] hover:bg-[var(--color-destructive)]/90" : ""}
          >
            {confirmNewGame ? "Confirm New?" : "New Game"}
          </Button>

          <Button
            onClick={() => sendAction("play_round")}
            disabled={!connected || !isIdle}
            className="bg-accent text-accent-foreground hover:bg-accent/90 active:scale-[0.98] transition-all duration-[var(--dur-micro)]"
          >
            Play Round
          </Button>

          <Button
            onClick={() => sendAction("end_session")}
            disabled={!connected}
            variant="outline"
          >
            End Session
          </Button>

          {[1, 5, 10].map((n) => (
            <Button
              key={n}
              onClick={() =>
                sendAction("auto_play", {
                  enabled: true,
                  delay_ms: 500,
                  rounds: n,
                })
              }
              disabled={!connected || auto_play}
              variant="outline"
            >
              +{n} round{n > 1 ? "s" : ""}
            </Button>
          ))}

          <Button
            onClick={() =>
              sendAction("auto_play", {
                enabled: !auto_play,
                delay_ms: 500,
                rounds: null,
              })
            }
            disabled={!connected}
            variant={auto_play ? "destructive" : "default"}
            className={auto_play ? "" : "active:scale-[0.98] transition-all duration-[var(--dur-micro)]"}
          >
            {auto_play ? "Stop Auto" : "Auto Play"}
          </Button>
        </div>
      </div>
    </div>
  );
}
