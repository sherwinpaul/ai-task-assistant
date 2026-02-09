"""Normalize raw API data into unified TaskSchema objects."""

from datetime import datetime
from typing import Any

from src.schemas.task_schema import TaskSchema


def normalize_jira(issue: dict[str, Any]) -> TaskSchema:
    """Convert a raw Jira issue dict into TaskSchema."""
    fields = issue.get("fields", {})
    assignee = fields.get("assignee")
    priority = fields.get("priority")
    due_date = None
    if fields.get("duedate"):
        try:
            due_date = datetime.fromisoformat(fields["duedate"])
        except (ValueError, TypeError):
            pass

    return TaskSchema(
        id=issue["key"],
        source="jira",
        title=fields.get("summary", ""),
        description=fields.get("description", "") or "",
        status=fields.get("status", {}).get("name") if fields.get("status") else None,
        priority=priority.get("name") if priority else None,
        assignee=assignee.get("displayName") if assignee else None,
        due_date=due_date,
        labels=fields.get("labels", []),
        url=f"{issue.get('self', '').split('/rest/')[0]}/browse/{issue['key']}",
        raw_metadata={
            "issue_type": fields.get("issuetype", {}).get("name"),
            "project": fields.get("project", {}).get("key"),
        },
    )


def normalize_gmail(message: dict[str, Any]) -> TaskSchema:
    """Convert a raw Gmail message dict into TaskSchema."""
    headers = {h["name"]: h["value"] for h in message.get("payload", {}).get("headers", [])}
    snippet = message.get("snippet", "")

    return TaskSchema(
        id=message["id"],
        source="gmail",
        title=headers.get("Subject", "(no subject)"),
        description=snippet,
        assignee=headers.get("From"),
        labels=message.get("labelIds", []),
        url=f"https://mail.google.com/mail/u/0/#inbox/{message['id']}",
        raw_metadata={
            "to": headers.get("To"),
            "date": headers.get("Date"),
            "thread_id": message.get("threadId"),
        },
    )


def normalize_calendar(event: dict[str, Any]) -> TaskSchema:
    """Convert a raw Google Calendar event dict into TaskSchema."""
    start = event.get("start", {})
    start_str = start.get("dateTime") or start.get("date")
    due_date = None
    if start_str:
        try:
            due_date = datetime.fromisoformat(start_str)
        except (ValueError, TypeError):
            pass

    organizer = event.get("organizer", {})
    attendees = event.get("attendees", [])

    return TaskSchema(
        id=event["id"],
        source="calendar",
        title=event.get("summary", "(no title)"),
        description=event.get("description", "") or "",
        status=event.get("status"),
        assignee=organizer.get("email"),
        due_date=due_date,
        url=event.get("htmlLink"),
        raw_metadata={
            "location": event.get("location"),
            "attendees": [a.get("email") for a in attendees],
            "end": event.get("end", {}).get("dateTime") or event.get("end", {}).get("date"),
        },
    )
