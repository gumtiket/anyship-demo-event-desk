from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Event(Base):
    __tablename__ = "desk_events"
    __table_args__ = (
        CheckConstraint(
            "capacity >= 1 AND occupied >= 0 AND occupied <= capacity", name="event_capacity_valid"
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(60))
    category: Mapped[str] = mapped_column(String(20))
    description: Mapped[str] = mapped_column(String(160))
    capacity: Mapped[int]
    occupied: Mapped[int] = mapped_column(default=0)


class Registration(Base):
    __tablename__ = "desk_registrations"
    __table_args__ = (UniqueConstraint("event_id", "nickname", name="event_nickname_unique"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("desk_events.id"), index=True)
    nickname: Mapped[str] = mapped_column(String(40))
    receipt: Mapped[str] = mapped_column(String(24))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    cancelled: Mapped[bool] = mapped_column(default=False)
