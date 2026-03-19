from __future__ import annotations

from pathlib import Path

from dodar.config import get_settings
from dodar.models.scoring import ScoringSession


def session_path(session_id: str) -> Path:
    return get_settings().scores_dir / f"{session_id}.json"


def save_session(session: ScoringSession) -> None:
    path = session_path(session.session_id)
    path.write_text(session.model_dump_json(indent=2))


def load_session(session_id: str) -> ScoringSession | None:
    path = session_path(session_id)
    if not path.exists():
        return None
    return ScoringSession.model_validate_json(path.read_text())


def load_all_sessions() -> list[ScoringSession]:
    settings = get_settings()
    sessions: list[ScoringSession] = []
    for path in sorted(settings.scores_dir.glob("*.json")):
        try:
            sessions.append(ScoringSession.model_validate_json(path.read_text()))
        except Exception:
            continue
    return sessions


def delete_session(session_id: str) -> bool:
    path = session_path(session_id)
    if path.exists():
        path.unlink()
        return True
    return False
