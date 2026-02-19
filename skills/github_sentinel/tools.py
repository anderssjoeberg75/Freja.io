from app.services.tool_registry import ToolRegistry
from pydantic import BaseModel, Field
from github import Github
from app.core.config import get_credential, settings
import logging

logger = logging.getLogger(__name__)

# --- Schemas ---

class IssueSchema(BaseModel):
    title: str = Field(..., description="Title of the issue.")
    body: str = Field(..., description="Body/Description of the issue.")
    repo_name: str = Field(..., description="Full repository name (e.g., 'owner/repo').")

class ListIssuesSchema(BaseModel):
    repo_name: str = Field(None, description="Repository to filter by. If None, lists all assigned issues.")

# --- Implementations ---

def _get_github_client():
    token = get_credential("GITHUB_TOKEN") or settings.GITHUB_TOKEN
    if not token:
        raise ValueError("GITHUB_TOKEN not found.")
    return Github(token)

def list_issues_impl(repo_name: str = None) -> str:
    """Lists issues assigned to the authenticated user."""
    try:
        g = _get_github_client()
        user = g.get_user()
        
        if repo_name:
            repo = g.get_repo(repo_name)
            issues = repo.get_issues(assignee=user.login)
        else:
            issues = user.get_issues(filter='assigned')
            
        if not issues.totalCount:
            return "No assigned issues found."
            
        output = f"### Assigned Issues (User: {user.login})\n"
        for issue in issues[:10]: # Limit to 10
            output += f"- [#{issue.number}] {issue.title} (Repo: {issue.repository.full_name})\n  Link: {issue.html_url}\n"
            
        return output
    except Exception as e:
        return f"Error listing issues: {e}"

def create_issue_impl(title: str, body: str, repo_name: str) -> str:
    """Creates a new issue in the specified repository."""
    try:
        g = _get_github_client()
        repo = g.get_repo(repo_name)
        issue = repo.create_issue(title=title, body=body)
        return f"Issue created successfully: {issue.html_url}"
    except Exception as e:
        return f"Error creating issue: {e}"

def check_notifications_impl() -> str:
    """Checks unread GitHub notifications."""
    try:
        g = _get_github_client()
        user = g.get_user()
        notifications = user.get_notifications()
        
        output = "### Unread Notifications\n"
        count = 0
        for notif in notifications[:10]:
            count += 1
            output += f"- **{notif.subject.type}**: {notif.subject.title} ({notif.repository.full_name})\n"
            
        if count == 0:
            return "No unread notifications."
            
        return output
    except Exception as e:
        return f"Error checking notifications: {e}"

# --- Registration ---

def register_tools(registry: ToolRegistry) -> None:
    registry.register(
        name="github_list_issues",
        description="List GitHub issues assigned to you.",
        args_schema=ListIssuesSchema,
    )(list_issues_impl)

    registry.register(
        name="github_create_issue",
        description="Create a new issue on GitHub.",
        args_schema=IssueSchema,
    )(create_issue_impl)
    
    registry.register(
        name="github_check_notifications",
        description="Check your unread GitHub notifications.",
        args_schema=BaseModel,
    )(check_notifications_impl)
