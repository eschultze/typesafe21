import asyncio
import json
import logging
import os
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")

from connection_manager import manager
from game_manager import GameManager

game_manager = GameManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    import database as db
    db.init_db()
    # Warm up the local Laya model in a background thread so the first
    # game round doesn't stall while weights load (~30s one-time per process).
    from rules.laya_ai import _get_agent
    asyncio.get_running_loop().run_in_executor(None, _get_agent)
    yield


app = FastAPI(title="TypeSafe21", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/history")
async def history():
    return game_manager.get_history()


@app.get("/api/history/{session_id}")
async def session_detail(session_id: int):
    return {
        "stats": game_manager.get_session_stats(session_id),
        "rounds": game_manager.get_session_rounds(session_id),
    }


@app.get("/api/leaderboard")
async def leaderboard():
    import database as db
    return {
        "single_turn": db.get_top_single_turn_profits(),
        "sessions": db.get_top_session_profits(),
    }


@app.get("/api/benchmark")
async def benchmark_endpoint(session_id: int | None = None):
    import benchmark
    return await asyncio.to_thread(benchmark.build_benchmark, session_id)


@app.websocket("/ws/{game_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str):
    await manager.connect(websocket, game_id)
    session = game_manager.get_or_create(game_id)

    try:
        # Send initial state
        await websocket.send_json({
            "type": "state_update",
            "state": session.get_state(),
        })

        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
                continue

            if not isinstance(data, dict):
                await websocket.send_json({"type": "error", "message": "Message must be a JSON object"})
                continue

            action = data.get("action")
            if not action:
                await websocket.send_json({"type": "error", "message": "Missing 'action' field"})
                continue

            if action == "new_game":
                state = session.new_game()
                await manager.broadcast(game_id, {
                    "type": "state_update",
                    "state": state,
                })

            elif action == "clear_database":
                # Wipe all persisted history, then start a fresh session so the
                # in-memory state does not reference a deleted session row.
                import database as db
                await asyncio.to_thread(db.clear_database)
                state = session.new_game()
                await manager.broadcast(game_id, {
                    "type": "state_update",
                    "state": state,
                })

            elif action == "play_round":
                if session.phase != "idle" or session.auto_play:
                    await websocket.send_json({"type": "error", "message": "Cannot play round: game is not in idle phase"})
                    continue
                async def broadcast(msg):
                    await manager.broadcast(game_id, msg)
                state = await session.play_round(broadcast_fn=broadcast)
                await manager.broadcast(game_id, {
                    "type": "state_update",
                    "state": state,
                })

            elif action == "auto_play":
                enabled = data.get("enabled", True)
                delay_ms = data.get("delay_ms", 500)
                delay_ms = max(100, min(delay_ms, 5000))
                rounds = data.get("rounds")
                session.set_auto_play(enabled, delay_ms, rounds)

                if enabled:
                    if session._auto_play_task and not session._auto_play_task.done():
                        session._auto_play_task.cancel()
                    async def broadcast(msg):
                        await manager.broadcast(game_id, msg)
                    session._auto_play_task = asyncio.create_task(session.auto_play_loop(broadcast))
                else:
                    session.auto_play = False
                    if session._auto_play_task and not session._auto_play_task.done():
                        session._auto_play_task.cancel()

                await manager.broadcast(game_id, {
                    "type": "state_update",
                    "state": session.get_state(),
                })

            elif action == "end_session":
                session.end_session()
                state = session.new_game()
                await manager.broadcast(game_id, {
                    "type": "state_update",
                    "state": state,
                })

            elif action == "get_state":
                await websocket.send_json({
                    "type": "state_update",
                    "state": session.get_state(),
                })

            else:
                await websocket.send_json({"type": "error", "message": f"Unknown action: {action}"})

    except WebSocketDisconnect:
        if session._auto_play_task and not session._auto_play_task.done():
            session._auto_play_task.cancel()
        manager.disconnect(websocket, game_id)
        game_manager.remove(game_id)
    except Exception as e:
        traceback.print_exc()
        if session._auto_play_task and not session._auto_play_task.done():
            session._auto_play_task.cancel()
        manager.disconnect(websocket, game_id)
        game_manager.remove(game_id)


if __name__ == "__main__":
    import signal
    import sys
    import uvicorn

    # NOTE: signal.signal is platform-limited (Unix only). For production,
    # use FastAPI's lifespan context manager for graceful shutdown.
    def handle_sigint(sig, frame):
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sigint)
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="error")
