from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from dodar.config import SCORING_DIMENSIONS
from dodar.models.scoring import DimensionScore, ScoreCard
from dodar.scoring.blind import create_scoring_session
from dodar.scoring.autoscore import autoscore_session
from dodar.storage.runs import load_result
from dodar.storage.scores import load_all_sessions, load_session, save_session, delete_session

router = APIRouter(tags=["scoring"])


SCORER_MODELS = {
    "claude-opus-4-6": "Claude Opus 4.6",
    "gpt-5.4": "GPT-5.4",
    "gpt-4o": "GPT-4o",
}


class CreateSessionRequest(BaseModel):
    scorer: str
    run_id: str  # which benchmark run to score
    auto_score: bool = False
    scorer_model: str = "claude-opus-4-6"  # which model to use for auto-scoring


class SubmitScoreRequest(BaseModel):
    scores: list[DimensionScore]


@router.post("/scoring/sessions")
async def create_session(req: CreateSessionRequest, request: Request) -> dict:
    scorer_label = SCORER_MODELS.get(req.scorer_model, req.scorer_model)
    session = create_scoring_session(
        scorer=req.scorer if not req.auto_score else f"{scorer_label}-auto ({req.scorer})",
        run_id=req.run_id,
    )
    save_session(session)

    if req.auto_score:
        import asyncio

        cancel_event = asyncio.Event()

        async def run_autoscore():
            await autoscore_session(session, concurrency=3, cancel_event=cancel_event, scorer_model=req.scorer_model)

        task = asyncio.create_task(run_autoscore())
        if not hasattr(request.app.state, "autoscore_tasks"):
            request.app.state.autoscore_tasks = {}
        if not hasattr(request.app.state, "autoscore_cancels"):
            request.app.state.autoscore_cancels = {}
        request.app.state.autoscore_tasks[session.session_id] = task
        request.app.state.autoscore_cancels[session.session_id] = cancel_event

    return {
        "session_id": session.session_id,
        "run_id": session.run_id,
        "total_items": len(session.items),
        "scorer": session.scorer,
        "auto_score": req.auto_score,
    }


@router.get("/scoring/scorer-models")
async def get_scorer_models() -> dict:
    return {"models": SCORER_MODELS}


@router.get("/scoring/sessions")
async def list_sessions() -> list[dict]:
    sessions = load_all_sessions()
    return [
        {
            "session_id": s.session_id,
            "scorer": s.scorer,
            "run_id": s.run_id,
            "created_at": s.created_at.isoformat(),
            "total_items": len(s.items),
            "scored_items": len(s.scores),
            "revealed": s.revealed,
        }
        for s in sessions
    ]


@router.get("/scoring/sessions/{session_id}/next")
async def get_next_item(session_id: str) -> dict:
    session = load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Find the next unscored item in order
    for item_id in session.order:
        if item_id not in session.scores:
            item = next((i for i in session.items if i.item_id == item_id), None)
            if not item:
                continue

            # Load the response text — try versioned run_id first, then unversioned
            result = load_result(item.run_result_file.replace(".json", ""))
            if not result:
                result = load_result(f"{item.scenario_id}_{item.model}_{item.condition}")
            if not result:
                continue

            position = session.order.index(item_id) + 1
            return {
                "item_id": item.item_id,
                "position": position,
                "total": len(session.items),
                "scenario_id": item.scenario_id,
                "scenario_prompt": result.prompt_sent,
                "response_text": result.response_text,
                "dimensions": SCORING_DIMENSIONS,
            }

    return {"complete": True, "total": len(session.items), "scored": len(session.scores)}


@router.post("/scoring/sessions/{session_id}/items/{item_id}/score")
async def submit_score(session_id: str, item_id: str, req: SubmitScoreRequest) -> dict:
    session = load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if item_id in session.scores:
        raise HTTPException(status_code=400, detail="Item already scored")

    # Validate all dimensions present
    provided = {s.dimension for s in req.scores}
    expected = set(SCORING_DIMENSIONS)
    if provided != expected:
        raise HTTPException(
            status_code=400,
            detail=f"Must provide scores for all dimensions. Missing: {expected - provided}",
        )

    session.scores[item_id] = ScoreCard(
        item_id=item_id,
        scores=req.scores,
        scored_at=datetime.now(timezone.utc),
    )
    save_session(session)

    return {"scored": len(session.scores), "total": len(session.items)}


@router.get("/scoring/sessions/{session_id}/progress")
async def get_progress(session_id: str) -> dict:
    session = load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"scored": len(session.scores), "total": len(session.items)}


@router.post("/scoring/sessions/{session_id}/retry")
async def retry_session(session_id: str, request: Request) -> dict:
    """Resume auto-scoring for an incomplete session."""
    session = load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    unscored = len(session.items) - len(session.scores)
    if unscored == 0:
        return {"status": "already_complete", "scored": len(session.scores), "total": len(session.items)}

    import asyncio

    cancel_event = asyncio.Event()

    async def run_retry():
        await autoscore_session(session, concurrency=3, cancel_event=cancel_event)

    task = asyncio.create_task(run_retry())
    if not hasattr(request.app.state, "autoscore_tasks"):
        request.app.state.autoscore_tasks = {}
    if not hasattr(request.app.state, "autoscore_cancels"):
        request.app.state.autoscore_cancels = {}
    request.app.state.autoscore_tasks[session_id] = task
    request.app.state.autoscore_cancels[session_id] = cancel_event

    return {"status": "retrying", "unscored": unscored, "total": len(session.items)}


@router.post("/scoring/sessions/{session_id}/stop")
async def stop_session(session_id: str, request: Request) -> dict:
    """Cancel a running auto-score task."""
    # Signal cancellation via event so pending items are skipped
    cancels = getattr(request.app.state, "autoscore_cancels", {})
    cancel_event = cancels.get(session_id)
    if cancel_event:
        cancel_event.set()
        cancels.pop(session_id, None)

    # Also cancel the task itself for any in-flight API calls
    tasks = getattr(request.app.state, "autoscore_tasks", {})
    task = tasks.get(session_id)
    if task and not task.done():
        task.cancel()
        tasks.pop(session_id, None)
        return {"status": "stopped", "session_id": session_id}

    return {"status": "not_running", "session_id": session_id}


@router.delete("/scoring/sessions/{session_id}")
async def delete_session_endpoint(session_id: str, request: Request) -> dict:
    """Stop and delete a scoring session."""
    # Signal cancellation
    cancels = getattr(request.app.state, "autoscore_cancels", {})
    cancel_event = cancels.pop(session_id, None)
    if cancel_event:
        cancel_event.set()

    # Cancel task
    tasks = getattr(request.app.state, "autoscore_tasks", {})
    task = tasks.get(session_id)
    if task and not task.done():
        task.cancel()
        tasks.pop(session_id, None)

    if delete_session(session_id):
        return {"status": "deleted", "session_id": session_id}
    raise HTTPException(status_code=404, detail="Session not found")


@router.post("/scoring/sessions/{session_id}/reveal")
async def reveal_session(session_id: str) -> dict:
    session = load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if len(session.scores) < len(session.items):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot reveal until all items are scored ({len(session.scores)}/{len(session.items)})",
        )

    session.revealed = True
    save_session(session)

    return {
        "revealed": True,
        "items": [
            {
                "item_id": item.item_id,
                "scenario_id": item.scenario_id,
                "model": item.model,
                "condition": item.condition,
                "scores": (
                    session.scores[item.item_id].model_dump()
                    if item.item_id in session.scores
                    else None
                ),
            }
            for item in session.items
        ],
    }
