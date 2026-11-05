import asyncio
import json
import threading
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from agent_brain import MatrixPopulationBrain

app = FastAPI(title="THE MATRIX - Live 3D Town Engine")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

brain = MatrixPopulationBrain(num_agents=100)
clients = set()
_loop_started = False

@app.on_event("startup")
async def start_tick_engine():
    global _loop_started
    if not _loop_started:
        _loop_started = True
        asyncio.create_task(simulation_loop())


async def simulation_loop():
    base_interval = 0.065  # 1.0x baseline tick interval (~15.4 ticks/sec)
    while True:
        payload = brain.step()
        dead = []
        for ws in list(clients):
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            clients.discard(ws)

        # Dynamically scale simulation tick delay based on Time Perception slider
        adjusted_delay = max(0.014, min(0.65, base_interval / max(0.1, brain.time_scale)))
        await asyncio.sleep(adjusted_delay)


@app.get("/map")
def get_town_map():
    return brain.town.get_static_map_data()


@app.get("/state")
def get_state():
    return brain.get_state_payload()


@app.post("/mode/{mode_name}")
def set_creator_mode(mode_name: str):
    brain.set_mode(mode_name)
    return {"status": "ok", "mode": brain.creator.current_mode}


@app.post("/timescale/{scale_val}")
def set_time_perception(scale_val: float):
    new_scale = brain.set_time_scale(scale_val)
    return {"status": "ok", "time_scale": new_scale}

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    clients.add(ws)
    try:
        await ws.send_json(brain.get_state_payload())
        while True:
            raw = await ws.receive_text()
            if raw in ("NEUTRAL", "HAPPY", "CHAOS"):
                brain.set_mode(raw)
            else:
                try:
                    cmd = json.loads(raw)
                    if cmd.get("type") == "MODE":
                        brain.set_mode(cmd.get("value", "NEUTRAL"))
                    elif cmd.get("type") == "TIME_SCALE":
                        brain.set_time_scale(float(cmd.get("value", 1.0)))
                except Exception:
                    pass
    except WebSocketDisconnect:
        clients.discard(ws)


def ensure_background_server(port: int = 8765) -> None:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(("127.0.0.1", port)) == 0:
            return

    def _run():
        uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")

    t = threading.Thread(target=_run, daemon=True)
    t.start()