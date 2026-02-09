from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TaskSchema(BaseModel):
    """Unified schema for tasks across Jira, Gmail, and Calendar."""

    id: str = Field(description="Unique identifier (e.g. PROJ-42, msg_abc123, evt_xyz)")
    source: str = Field(description="Origin system: jira | gmail | calendar")
    title: str = Field(description="Task/subject title")
    description: str = Field(default="", description="Full body or description text")
    status: Optional[str] = Field(default=None, description="Status (e.g. To Do, In Progress)")
    priority: Optional[str] = Field(default=None, description="Priority level")
    assignee: Optional[str] = Field(default=None, description="Assigned person")
    due_date: Optional[datetime] = Field(default=None, description="Due date or event time")
    labels: list[str] = Field(default_factory=list, description="Tags or labels")
    url: Optional[str] = Field(default=None, description="Link back to original item")
    raw_metadata: dict = Field(default_factory=dict, description="Extra source-specific data")

    def to_document_text(self) -> str:
        """Flatten into a single string for embedding."""
        parts = [
            f"[{self.source.upper()}] {self.title}",
            f"ID: {self.id}",
        ]
        if self.status:
            parts.append(f"Status: {self.status}")
        if self.priority:
            parts.append(f"Priority: {self.priority}")
        if self.assignee:
            parts.append(f"Assignee: {self.assignee}")
        if self.due_date:
            parts.append(f"Due: {self.due_date.isoformat()}")
        if self.labels:
            parts.append(f"Labels: {', '.join(self.labels)}")
        if self.description:
            parts.append(f"Description: {self.description[:500]}")
        if self.url:
            parts.append(f"URL: {self.url}")
        return "\n".join(parts)
