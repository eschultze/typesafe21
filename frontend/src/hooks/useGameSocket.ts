"use client";

import { useEffect, useRef } from "react";
import { useGameStore } from "@/stores/gameStore";

export function useGameSocket(gameId: string) {
  const wsRef = useRef<WebSocket | null>(null);
  const { setConnected, setWebSocket, updateState } = useGameStore();

  useEffect(() => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//localhost:8000/ws/${gameId}`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      setWebSocket(ws);
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === "state_update" && msg.state) {
          updateState(msg.state);
        }
      } catch (e) {
        console.error("Failed to parse WS message:", e);
      }
    };

    ws.onclose = () => {
      setConnected(false);
      setWebSocket(null);
    };

    ws.onerror = (err) => {
      console.error("WebSocket error:", err);
      setConnected(false);
    };

    return () => {
      ws.close();
      setConnected(false);
      setWebSocket(null);
    };
  }, [gameId, setConnected, setWebSocket, updateState]);
}
