"""Read-only Gmail + Google Calendar LangChain tools."""

import json
import logging
from datetime import datetime, timedelta, timezone

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from langchain_core.tools import tool

from src.config.settings import settings

logger = logging.getLogger(__name__)

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
ALL_SCOPES = GMAIL_SCOPES + CALENDAR_SCOPES

_credentials: Credentials | None = None


def get_google_credentials() -> Credentials:
    """Load or refresh Google OAuth credentials."""
    global _credentials
    if _credentials and _credentials.valid:
        return _credentials

    import os

    if os.path.exists(settings.google_token_file):
        _credentials = Credentials.from_authorized_user_file(
            settings.google_token_file, ALL_SCOPES
        )

    if not _credentials or not _credentials.valid:
        if _credentials and _credentials.expired and _credentials.refresh_token:
            _credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                settings.google_credentials_file, ALL_SCOPES
            )
            _credentials = flow.run_local_server(port=0)
        with open(settings.google_token_file, "w") as f:
            f.write(_credentials.to_json())

    return _credentials


_gmail_service = None
_calendar_service = None


def get_gmail_service():
    global _gmail_service
    if _gmail_service is None:
        creds = get_google_credentials()
        _gmail_service = build("gmail", "v1", credentials=creds)
    return _gmail_service


def get_calendar_service():
    global _calendar_service
    if _calendar_service is None:
        creds = get_google_credentials()
        _calendar_service = build("calendar", "v3", credentials=creds)
    return _calendar_service


# --- Gmail Tools ---


@tool
def gmail_get_thread(thread_id: str) -> str:
    """Get a Gmail thread by its ID. Returns JSON with messages in the thread.

    Args:
        thread_id: The Gmail thread ID.
    """
    service = get_gmail_service()
    thread = service.users().threads().get(userId="me", id=thread_id, format="metadata").execute()
    return json.dumps(thread, default=str)


@tool
def gmail_search_messages(query: str = "", max_results: int = 10) -> str:
    """Search Gmail messages. Returns JSON array of message summaries.

    Args:
        query: Gmail search query (e.g. 'is:unread', 'from:boss@company.com', 'subject:urgent').
        max_results: Maximum number of messages to return (default 10).
    """
    service = get_gmail_service()
    results = (
        service.users()
        .messages()
        .list(userId="me", q=query or "is:inbox", maxResults=max_results)
        .execute()
    )
    messages = results.get("messages", [])
    if not messages:
        return "[]"

    # Batch-fetch all messages in parallel instead of serial loop
    detailed = [None] * len(messages)

    def _make_callback(idx):
        def _cb(req_id, response, exception):
            if exception is None:
                headers = {h["name"]: h["value"] for h in response.get("payload", {}).get("headers", [])}
                detailed[idx] = {
                    "id": response["id"],
                    "threadId": response.get("threadId"),
                    "snippet": response.get("snippet", ""),
                    "from": headers.get("From", ""),
                    "to": headers.get("To", ""),
                    "subject": headers.get("Subject", ""),
                    "date": headers.get("Date", ""),
                }
        return _cb

    batch = service.new_batch_http_request()
    for i, msg_ref in enumerate(messages):
        batch.add(
            service.users().messages().get(
                userId="me", id=msg_ref["id"], format="metadata",
                metadataHeaders=["From", "To", "Subject", "Date"],
            ),
            callback=_make_callback(i),
        )
    batch.execute()

    return json.dumps([d for d in detailed if d is not None], default=str)


# --- Calendar Tools ---


@tool
def gcal_list_events(days_ahead: int = 7, max_results: int = 20) -> str:
    """List upcoming Google Calendar events. Returns JSON array of events.

    Args:
        days_ahead: Number of days ahead to look (default 7).
        max_results: Maximum number of events to return (default 20).
    """
    service = get_calendar_service()
    now = datetime.now(timezone.utc)
    time_max = now + timedelta(days=days_ahead)

    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=now.isoformat(),
            timeMax=time_max.isoformat(),
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    return json.dumps(events_result.get("items", []), default=str)


@tool
def gcal_get_event(event_id: str) -> str:
    """Get a single Google Calendar event by its ID. Returns JSON.

    Args:
        event_id: The Google Calendar event ID.
    """
    service = get_calendar_service()
    event = service.events().get(calendarId="primary", eventId=event_id).execute()
    return json.dumps(event, default=str)


def get_google_tools() -> list:
    return [gmail_get_thread, gmail_search_messages, gcal_list_events, gcal_get_event]
