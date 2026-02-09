"""SQLAlchemy Reminder model and database initialization."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.config.settings import settings


class Base(DeclarativeBase):
    pass


class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message = Column(Text, nullable=False)
    remind_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="pending")  # pending | fired | cancelled
    reference_id = Column(String(100), nullable=True)  # e.g. PROJ-42

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "message": self.message,
            "remind_at": self.remind_at.isoformat() if self.remind_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "status": self.status,
            "reference_id": self.reference_id,
        }


_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(f"sqlite:///{settings.sqlite_db_path}", echo=False)
        Base.metadata.create_all(_engine)
    return _engine


def get_session() -> Session:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine())
    return _SessionLocal()
