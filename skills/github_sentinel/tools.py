from app.services.tool_registry import ToolRegistry
from pydantic import BaseModel, Field
from app.core.config import get_credential, settings
import logging
import asyncio

logger = logging.getLogger(__name__)

# --- Schemas ---

class IssueSchema(BaseModel):
    issue_title: str = Field(..., description="Title of the issue.")
    body: str = Field(..., description="Body/Description of the issue.")
    repo_name: str = Field(..., description="Full repository name (e.g., 'owner/repo').")

class ListIssuesSchema(BaseModel):
    repo_name: str = Field(None, description="Repository to filter by. If None, lists all assigned issues.")

class CheckNotificationsSchema(BaseModel):
    pass

# --- Helpers ---

def _get_github_client():
    try:
        from github import Github
    except ImportError:
        raise RuntimeError("PyGithub not installed. Run: pip install PyGithub")
    token = get_credential("GITHUB_TOKEN") or getattr(settings, "GITHUB_TOKEN", None)
    if not token:
        raise ValueError("GITHUB_TOKEN saknas. Konfigurera det i inställningarna.")
    return Github(token)

# --- Implementations (async wrappers) ---

async def list_issues_impl(repo_name: str = None) -> str:
    """Lists issues assigned to the authenticated user."""
    loop = asyncio.get_event_loop()

    def _sync():
        try:
            g = _get_github_client()
            user = g.get_user()
            if repo_name:
                repo = g.get_repo(repo_name)
                issues = repo.get_issues(assignee=user.login)
            else:
                issues = user.get_issues(filter='assigned')
            if not issues.totalCount:
                return "Inga tilldelade issues hittades."
            output = f"Tilldelade Issues (Användare: {user.login})\n"
            for issue in issues[:10]:
                output += f"- [#{issue.number}] {issue.title} ({issue.repository.full_name})\n  {issue.html_url}\n"
            return output
        except Exception as e:
            return f"Fel vid hämtning av issues: {e}"

    return await loop.run_in_executor(None, _sync)

async def create_issue_impl(issue_title: str, body: str, repo_name: str) -> str:
    """Creates a new issue in the specified repository."""
    loop = asyncio.get_event_loop()

    def _sync():
        try:
            g = _get_github_client()
            repo = g.get_repo(repo_name)
            issue = repo.create_issue(title=issue_title, body=body)
            return f"Issue skapad: {issue.html_url}"
        except Exception as e:
            return f"Fel vid skapande av issue: {e}"

    return await loop.run_in_executor(None, _sync)

async def check_notifications_impl() -> str:
    """Checks unread GitHub notifications."""
    loop = asyncio.get_event_loop()

    def _sync():
        try:
            g = _get_github_client()
            user = g.get_user()
            notifications = user.get_notifications()
            output = "Olästa notifikationer:\n"
            count = 0
            for notif in notifications[:10]:
                count += 1
                output += f"- {notif.subject.type}: {notif.subject.title} ({notif.repository.full_name})\n"
            if count == 0:
                return "Inga olästa notifikationer."
            return output
        except Exception as e:
            return f"Fel vid hämtning av notifikationer: {e}"

    return await loop.run_in_executor(None, _sync)

# --- Registration ---

def register_tools(registry: ToolRegistry) -> None:
    registry.register(
        name="github_list_issues",
        description="Lista GitHub-issues tilldelade till dig.",
        args_schema=ListIssuesSchema,
    )(list_issues_impl)

    registry.register(
        name="github_create_issue",
        description="Skapa ett nytt issue på GitHub.",
        args_schema=IssueSchema,
    )(create_issue_impl)

    registry.register(
        name="github_check_notifications",
        description="Kolla olästa GitHub-notifikationer.",
        args_schema=CheckNotificationsSchema,
    )(check_notifications_impl)
