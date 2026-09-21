"use client";

import { useState } from "react";
import { useGameStore } from "@/stores/gameStore";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export function GameControls() {
  const { phase, auto_play, round_number } = useGameStore((s) => s.state);
  const sendAction = useGameStore((s) => s.sendAction);
  const connected = useGameStore((s) => s.connected);
  const [autoRounds, setAutoRounds] = useState(50);

  const isIdle = phase === "idle";

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center gap-2">
        <Badge variant={connected ? "default" : "destructive"}>
          {connected ? "Connected" : "Disconnected"}
        </Badge>
        {round_number > 0 && (
          <Badge variant="secondary">Round {round_number}</Badge>
        )}
        {auto_play && (
          <Badge className="bg-blue-600">Auto-Playing</Badge>
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
          onClick={() => sendAction("continue_game")}
          disabled={!connected}
          variant="outline"
        >
          Continue
        </Button>

        <Button
          onClick={() => sendAction("play_round")}
          disabled={!connected || !isIdle}
          className="bg-green-600 hover:bg-green-700"
        >
          Play Round
        </Button>

        <Button
          onClick={() =>
            sendAction("auto_play", {
              enabled: !auto_play,
              delay_ms: 500,
              rounds: autoRounds,
            })
          }
          disabled={!connected}
          variant={auto_play ? "destructive" : "default"}
        >
          {auto_play ? "Stop Auto" : "Auto Play"}
        </Button>

        {auto_play && (
          <Button
            onClick={() => sendAction("auto_play", { enabled: false })}
            variant="destructive"
          >
            Stop
          </Button>
        )}
      </div>

      {!auto_play && (
        <div className="flex items-center gap-2 text-sm">
          <label className="text-muted-foreground">Auto rounds:</label>
          <input
            type="number"
            value={autoRounds}
            onChange={(e) => setAutoRounds(Number(e.target.value))}
            className="w-20 px-2 py-1 rounded bg-white/10 border border-white/20 text-sm"
            min={1}
            max={1000}
          />
        </div>
      )}
    </div>
  );
}
