"use client";

import { useEffect, useRef } from "react";
import { useGameStore } from "@/stores/gameStore";

const MAX_RECONNECT_DELAY = 30000;
const INITIAL_RECONNECT_DELAY = 1000;

export function useGameSocket(gameId: string) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectDelay = useRef(INITIAL_RECONNECT_DELAY);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const closedRef = useRef(false);
  const { setConnected, setWebSocket, updateState } = useGameStore();

  useEffect(() => {
    function connect() {
      // Next.js rewrites (rewrites in next.config) don't proxy WebSocket
      // connections, so we must connect directly to the backend.
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const wsHost = process.env.NEXT_PUBLIC_WS_HOST || window.location.hostname;
      const wsPort = process.env.NEXT_PUBLIC_WS_PORT || "8000";
      const wsUrl = `${protocol}//${wsHost}:${wsPort}/ws/${gameId}`;

      closedRef.current = false;
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        setWebSocket(ws);
        reconnectDelay.current = INITIAL_RECONNECT_DELAY;
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
        if (closedRef.current) return;
        setConnected(false);
        setWebSocket(null);
        scheduleReconnect();
      };

      ws.onerror = () => {
        setConnected(false);
      };
    }

    function scheduleReconnect() {
      if (reconnectTimer.current) return;
      reconnectTimer.current = setTimeout(() => {
        reconnectTimer.current = null;
        reconnectDelay.current = Math.min(reconnectDelay.current * 2, MAX_RECONNECT_DELAY);
        connect();
      }, reconnectDelay.current);
    }

    connect();

    return () => {
      closedRef.current = true;
      if (reconnectTimer.current) {
        clearTimeout(reconnectTimer.current);
        reconnectTimer.current = null;
      }
      wsRef.current?.close();
      setConnected(false);
      setWebSocket(null);
    };
  }, [gameId, setConnected, setWebSocket, updateState]);
}
