"""APScheduler-based reminder scheduler + LangChain tools."""

import json
import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from langchain_core.tools import tool

from src.reminders.models import Reminder, get_session

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def get_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler()
        _scheduler.start()
        logger.info("APScheduler started")
    return _scheduler


def _fire_reminder(reminder_id: int) -> None:
    """Callback when a reminder fires."""
    session = get_session()
    try:
        reminder = session.query(Reminder).get(reminder_id)
        if reminder and reminder.status == "pending":
            reminder.status = "fired"
            session.commit()
            logger.info("Reminder fired: [%d] %s", reminder_id, reminder.message)
    finally:
        session.close()


@tool
def create_reminder(message: str, remind_at: str, reference_id: str = "") -> str:
    """Create a local reminder that fires at the specified time.

    Args:
        message: The reminder message (e.g. 'Check status of PROJ-42').
        remind_at: ISO 8601 datetime string for when to fire (e.g. '2025-01-15T09:00:00').
        reference_id: Optional reference to a task ID (e.g. 'PROJ-42').
    """
    try:
        fire_time = datetime.fromisoformat(remind_at)
    except ValueError:
        return json.dumps({"error": f"Invalid datetime format: {remind_at}. Use ISO 8601."})

    if fire_time < datetime.now():
        return json.dumps({"error": f"Cannot set a reminder in the past ({remind_at}). Please use a future date/time."})

    session = get_session()
    try:
        reminder = Reminder(
            message=message,
            remind_at=fire_time,
            reference_id=reference_id or None,
        )
        session.add(reminder)
        session.commit()
        reminder_id = reminder.id

        scheduler = get_scheduler()
        scheduler.add_job(
            _fire_reminder,
            "date",
            run_date=fire_time,
            args=[reminder_id],
            id=f"reminder_{reminder_id}",
        )

        return json.dumps({
            "status": "created",
            "reminder": reminder.to_dict(),
        }, default=str)
    finally:
        session.close()


@tool
def list_reminders(status: str = "pending") -> str:
    """List reminders filtered by status.

    Args:
        status: Filter by status: 'pending', 'fired', or 'all' (default 'pending').
    """
    session = get_session()
    try:
        query = session.query(Reminder)
        if status != "all":
            query = query.filter(Reminder.status == status)
        reminders = query.order_by(Reminder.remind_at).all()
        return json.dumps([r.to_dict() for r in reminders], default=str)
    finally:
        session.close()


def get_reminder_tools() -> list:
    return [create_reminder, list_reminders]
