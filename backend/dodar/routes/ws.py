from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from dodar.engine.progress import ProgressEvent

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/runs/{run_id}")
async def run_progress_ws(websocket: WebSocket, run_id: str):
    await websocket.accept()

    # Get the tracker for this run
    trackers = getattr(websocket.app.state, "run_trackers", {})
    tracker = trackers.get(run_id)

    if not tracker:
        await websocket.send_json({"type": "error", "error": "Run not found"})
        await websocket.close()
        return

    queue: asyncio.Queue[ProgressEvent] = asyncio.Queue()

    def on_event(event: ProgressEvent) -> None:
        queue.put_nowait(event)

    tracker.add_listener(on_event)

    try:
        while True:
            # Wait for events with a timeout to allow checking for client messages
            try:
                event = await asyncio.wait_for(queue.get(), timeout=1.0)
                try:
                    await websocket.send_json(event.to_dict())
                except (RuntimeError, WebSocketDisconnect):
                    break
                if event.type.value in ("run_complete", "run_error"):
                    break
            except asyncio.TimeoutError:
                # Check if client sent a cancel message
                try:
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=0.01)
                    msg = json.loads(data)
                    if msg.get("type") == "cancel":
                        task = websocket.app.state.active_runs.get(run_id)
                        if task and not task.done():
                            task.cancel()
                        break
                except (asyncio.TimeoutError, Exception):
                    pass
    except (WebSocketDisconnect, RuntimeError):
        pass
    finally:
        tracker.remove_listener(on_event)
