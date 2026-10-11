import os
import hashlib
import hmac
import secrets
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import SECRET_KEY
from app.db import get_session
from app.logging_config import logger
from app.models import Event, Registration

app = FastAPI(title="Event Desk", version="1.0.0")
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")
Database = Annotated[Session, Depends(get_session)]


class JoinRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    event_id: int = Field(strict=True, ge=1)
    nickname: str = Field(min_length=1, max_length=40)


class CancelRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    receipt: str = Field(pattern=r"^[0-9a-f]{24}$")


def event_view(event: Event) -> dict:
    return {
        "id": event.id,
        "title": event.title,
        "category": event.category,
        "description": event.description,
        "capacity": event.capacity,
        "occupied": event.occupied,
        "remaining": event.capacity - event.occupied,
    }


def registration_view(registration: Registration, title: str) -> dict:
    return {
        "id": registration.id,
        "event_id": registration.event_id,
        "title": title,
        "nickname": registration.nickname,
        "receipt": registration.receipt,
        "created_at": registration.created_at.isoformat(),
        "cancelled": registration.cancelled,
    }


@app.exception_handler(SQLAlchemyError)
def database_failure(_request: Request, _error: SQLAlchemyError) -> JSONResponse:
    logger.warning("database_request_failed")
    return JSONResponse(
        status_code=503, content={"detail": "DB 연결과 초기화 상태를 확인해 주세요."}
    )


@app.get("/")
def home() -> FileResponse:
    return FileResponse(static_dir / "index.html")


@app.get("/api/events")
def events(session: Database) -> list[dict]:
    return [event_view(event) for event in session.scalars(select(Event).order_by(Event.id))]


@app.get("/api/registrations")
def registrations(session: Database) -> list[dict]:
    rows = session.execute(
        select(Registration, Event.title).join(Event).order_by(Registration.id.desc()).limit(100)
    )
    return [registration_view(registration, title) for registration, title in rows]


@app.post("/api/registrations", status_code=201)
def join(body: JoinRequest, session: Database) -> dict:
    with session.begin():
        event = session.scalar(select(Event).where(Event.id == body.event_id).with_for_update())
        if event is None:
            raise HTTPException(404, "모임을 찾지 못했어요.")
        if event.occupied >= event.capacity:
            raise HTTPException(409, "정원이 마감됐어요. 다른 모임을 선택해 주세요.")
        previous = session.scalar(
            select(Registration).where(
                Registration.event_id == event.id, Registration.nickname == body.nickname
            )
        )
        if previous is not None:
            raise HTTPException(409, "이미 신청한 닉네임이에요. 다른 닉네임을 사용해 주세요.")
        receipt = hmac.new(
            SECRET_KEY.encode(), secrets.token_bytes(16), hashlib.sha256
        ).hexdigest()[:24]
        record = Registration(
            event_id=event.id,
            nickname=body.nickname,
            receipt=receipt,
            created_at=datetime.now(UTC),
            cancelled=False,
        )
        event.occupied += 1
        session.add(record)
        session.flush()
        result = registration_view(record, event.title)
        logger.info("registration_created event_id=%s record_id=%s", event.id, record.id)
    return result


@app.post("/api/registrations/{registration_id}/cancel")
def cancel(registration_id: int, body: CancelRequest, session: Database) -> dict:
    with session.begin():
        record = session.get(Registration, registration_id)
        if record is None:
            raise HTTPException(404, "신청 기록을 찾지 못했어요.")
        event = session.scalar(select(Event).where(Event.id == record.event_id).with_for_update())
        session.refresh(record)
        if not hmac.compare_digest(body.receipt, record.receipt):
            raise HTTPException(403, "접수 번호가 맞지 않아요.")
        if record.cancelled:
            raise HTTPException(409, "이미 취소한 신청이에요.")
        record.cancelled = True
        event.occupied -= 1
        logger.info("registration_cancelled event_id=%s record_id=%s", event.id, record.id)
        result = registration_view(record, event.title)
    return result


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))


@app.get("/healthz")
def _bronze_healthz() -> dict[str, str]:
    return {"status": "ok"}
