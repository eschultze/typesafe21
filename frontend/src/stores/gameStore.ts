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
  ai_bet_history: number[];
  ai_confidence_history: number[];
  prev_bets: number[];
  chipsAnimating: boolean;

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
      ai_bet_history: [],
      ai_confidence_history: [],
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
          updates.ai_bet_history = [];
          updates.ai_confidence_history = [];
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
          const aiHand = result.hands?.find(
            (h: any) => h.is_ai && h.name === "You"
          );
          if (aiHand) {
            updates.ai_bet_history = [...get().ai_bet_history, aiHand.bet];
            updates.ai_confidence_history = [
              ...get().ai_confidence_history,
              aiHand.confidence,
            ];
          }
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
