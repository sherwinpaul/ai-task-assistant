"""Read-only Jira LangChain tools."""

import json
import logging

from jira import JIRA
from langchain_core.tools import tool

from src.config.settings import settings

logger = logging.getLogger(__name__)

_client: JIRA | None = None


def get_jira_client() -> JIRA:
    global _client
    if _client is None:
        _client = JIRA(
            server=settings.jira_server,
            basic_auth=(settings.jira_email, settings.jira_api_token),
        )
    return _client


def _issue_to_dict(issue) -> dict:
    fields = issue.fields
    return {
        "key": issue.key,
        "fields": {
            "summary": fields.summary,
            "description": fields.description or "",
            "status": {"name": fields.status.name} if fields.status else None,
            "priority": {"name": fields.priority.name} if fields.priority else None,
            "assignee": {"displayName": fields.assignee.displayName} if fields.assignee else None,
            "duedate": str(fields.duedate) if fields.duedate else None,
            "labels": fields.labels or [],
            "issuetype": {"name": fields.issuetype.name} if fields.issuetype else None,
            "project": {"key": fields.project.key} if fields.project else None,
        },
        "self": issue.self,
    }


@tool
def jira_list_issues(project_key: str = "", max_results: int = 50) -> str:
    """List Jira issues for a project. Returns JSON array of issues.

    Args:
        project_key: Jira project key (e.g. PROJ). Defaults to configured project.
        max_results: Maximum number of issues to return (default 50).
    """
    client = get_jira_client()
    pk = project_key or settings.jira_project_key
    jql = f"project = {pk} ORDER BY updated DESC"
    issues = client.search_issues(jql, maxResults=max_results)
    return json.dumps([_issue_to_dict(i) for i in issues], default=str)


@tool
def jira_get_issue(issue_key: str) -> str:
    """Get a single Jira issue by its key (e.g. PROJ-42). Returns JSON.

    Args:
        issue_key: The Jira issue key (e.g. PROJ-42).
    """
    client = get_jira_client()
    issue = client.issue(issue_key)
    return json.dumps(_issue_to_dict(issue), default=str)


@tool
def jira_search_issues(jql: str, max_results: int = 20) -> str:
    """Search Jira issues using JQL. Returns JSON array of matching issues.

    Args:
        jql: JQL query string (e.g. 'status = "In Progress" AND assignee = currentUser()').
        max_results: Maximum number of results (default 20).
    """
    client = get_jira_client()
    issues = client.search_issues(jql, maxResults=max_results)
    return json.dumps([_issue_to_dict(i) for i in issues], default=str)


def get_jira_tools() -> list:
    return [jira_list_issues, jira_get_issue, jira_search_issues]
