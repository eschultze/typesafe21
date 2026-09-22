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
  played_ranks: Record<string, number>;
}

export type GamePhase = "idle" | "betting" | "dealing" | "player_turn" | "dealer_turn" | "results";

export interface LastAction {
  type: string;
  player?: string;
  action?: string;
  result?: {
    hands?: Array<{
      hand: string[];
      result: string;
      payout: number;
      name: string;
      bet: number;
      confidence: number;
      is_ai?: boolean;
      decision?: string;
    }>;
    [key: string]: unknown;
  };
  round_number?: number;
  [key: string]: unknown;
}

export interface GameState {
  phase: GamePhase;
  round_number: number;
  players: PlayerData[];
  dealer: HandData | null;
  dealer_hidden: boolean;
  shoe: ShoeData;
  current_player: string | null;
  last_action: LastAction | null;
  session_id: number | null;
  auto_play: boolean;
  auto_play_delay_ms: number;
}

interface GameStore {
  connected: boolean;
  game_id: string;
  state: GameState;
  ws: WebSocket | null;
  player_histories: Record<string, { bets: number[]; confidences: number[] }>;
  prev_bets: number[];
  chipsAnimating: boolean;

  setConnected: (connected: boolean) => void;
  setWebSocket: (ws: WebSocket | null) => void;
  setGameId: (id: string) => void;
  updateState: (state: GameState) => void;
  sendAction: (action: string, data?: Record<string, unknown>) => void;
}

const defaultState: GameState = {
  phase: "idle",
  round_number: 0,
  players: [],
  dealer: null,
  dealer_hidden: true,
  shoe: { remaining: 0, total: 312, running_count: 0, true_count: 0, penetration_pct: 0, played_ranks: {} },
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
      player_histories: {},
      prev_bets: [],
      chipsAnimating: false,

      setConnected: (connected) => set({ connected }),
      setWebSocket: (ws) => set({ ws }),
      setGameId: (id) => set({ game_id: id }),
      updateState: (state) => {
        const prev = get().state;
        const lastAction = state.last_action;

        const updates: Partial<GameStore> = { state };

        // Detect new game (round_number resets to 0 after being > 0)
        if (state.round_number === 0 && prev.round_number > 0) {
          updates.player_histories = {};
        }

        // Detect bet changes → trigger chip animation
        const newBets = state.players.map((p) => p.current_bet);
        const oldBets = get().prev_bets;
        const betsChanged =
          oldBets.length === 0 ||
          newBets.some((b, i) => b !== (oldBets[i] || 0));

        if (betsChanged && state.phase !== "idle") {
          updates.prev_bets = newBets;
          updates.chipsAnimating = true;
          setTimeout(() => {
            get().chipsAnimating && set({ chipsAnimating: false });
          }, state.auto_play ? 150 : 300);
        }

        // Reset chips when round ends
        if (state.phase === "idle" && prev.phase !== "idle") {
          updates.prev_bets = state.players.map(() => 0);
          updates.chipsAnimating = true;
          setTimeout(() => set({ chipsAnimating: false }), 200);
        }

        if (
          lastAction?.type === "round_result" &&
          state.round_number > prev.round_number
        ) {
          const result = lastAction.result;
          const histories = { ...get().player_histories };
          for (const h of result?.hands ?? []) {
            const name = h.name as string;
            if (!histories[name]) {
              histories[name] = { bets: [], confidences: [] };
            }
            histories[name].bets.push(h.bet);
            histories[name].confidences.push(h.confidence);
          }
          updates.player_histories = histories;
        }

        set(updates);
      },
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
