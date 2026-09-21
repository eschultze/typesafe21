import asyncio
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from connection_manager import manager
from game_manager import GameManager

game_manager = GameManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    import database as db
    db.init_db()
    yield


app = FastAPI(title="TypeSafe21", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
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
            data = json.loads(raw)
            action = data.get("action")

            if action == "new_game":
                state = session.new_game()
                await manager.broadcast(game_id, {
                    "type": "state_update",
                    "state": state,
                })

            elif action == "continue_game":
                state = session.continue_game()
                await manager.broadcast(game_id, {
                    "type": "state_update",
                    "state": state,
                })

            elif action == "play_round":
                state = session.play_round()
                await manager.broadcast(game_id, {
                    "type": "state_update",
                    "state": state,
                })

            elif action == "auto_play":
                enabled = data.get("enabled", True)
                delay_ms = data.get("delay_ms", 500)
                rounds = data.get("rounds")
                session.set_auto_play(enabled, delay_ms, rounds)

                if enabled:
                    async def broadcast(msg):
                        await manager.broadcast(game_id, msg)
                    asyncio.create_task(session.auto_play_loop(broadcast))
                else:
                    session.auto_play = False

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

    except WebSocketDisconnect:
        manager.disconnect(websocket, game_id)
    except Exception as e:
        manager.disconnect(websocket, game_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
