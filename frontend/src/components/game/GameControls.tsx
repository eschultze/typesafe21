"use client";

import { useGameStore } from "@/stores/gameStore";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export function GameControls() {
  const { phase, auto_play, round_number } = useGameStore((s) => s.state);
  const sendAction = useGameStore((s) => s.sendAction);
  const connected = useGameStore((s) => s.connected);

  const isIdle = phase === "idle";

  return (
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
          onClick={() => sendAction("new_game")}
          disabled={!connected}
          variant="outline"
        >
          New Game
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
  );
}
