import { create } from "zustand";
import { devtools } from "zustand/middleware";

export interface CardData {
  rank: string;
  suit: string;
  value: number;
}

export interface HandData {
  cards: CardData[];
  value: number;
  is_soft: boolean;
  is_bust: boolean;
  is_blackjack: boolean;
}

export interface PlayerData {
  name: string;
  balance: number;
  current_bet: number;
  wins: number;
  losses: number;
  pushes: number;
  hand: HandData;
  balance_history: number[];
}

export interface ShoeData {
  remaining: number;
  total: number;
  running_count: number;
  true_count: number;
  penetration_pct: number;
}

export interface GameState {
  phase: string;
  round_number: number;
  players: PlayerData[];
  dealer: HandData | null;
  dealer_hidden: boolean;
  shoe: ShoeData;
  current_player: string | null;
  last_action: any;
  session_id: number | null;
  auto_play: boolean;
  auto_play_delay_ms: number;
}

interface GameStore {
  connected: boolean;
  game_id: string;
  state: GameState;
  ws: WebSocket | null;

  setConnected: (connected: boolean) => void;
  setWebSocket: (ws: WebSocket | null) => void;
  setGameId: (id: string) => void;
  updateState: (state: GameState) => void;
  sendAction: (action: string, data?: Record<string, any>) => void;
}

const defaultState: GameState = {
  phase: "idle",
  round_number: 0,
  players: [],
  dealer: null,
  dealer_hidden: true,
  shoe: { remaining: 0, total: 312, running_count: 0, true_count: 0, penetration_pct: 0 },
  current_player: null,
  last_action: null,
  session_id: null,
  auto_play: false,
  auto_play_delay_ms: 500,
};

export const useGameStore = create<GameStore>()(
  devtools(
    (set, get) => ({
      connected: false,
      game_id: "default",
      state: defaultState,
      ws: null,

      setConnected: (connected) => set({ connected }),
      setWebSocket: (ws) => set({ ws }),
      setGameId: (id) => set({ game_id: id }),
      updateState: (state) => set({ state }),
      sendAction: (action, data = {}) => {
        const ws = get().ws;
        if (ws && ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ action, ...data }));
        }
      },
    }),
    { name: "GameStore" }
  )
);
