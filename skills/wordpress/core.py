"""Core helpers for publishing posts to a WordPress blog via REST API."""

from __future__ import annotations

import os
from typing import Any

import httpx


class WordPressConfigError(RuntimeError):
    """Raised when required WordPress configuration is missing."""


class WordPressPublishError(RuntimeError):
    """Raised when WordPress rejects a publish request."""


def _get_config() -> tuple[str, str, str]:
    from app.core.config import get_credential
    base_url = get_credential("WORDPRESS_BASE_URL", "").strip().rstrip("/")
    username = get_credential("WORDPRESS_USERNAME", "").strip()
    app_password = get_credential("WORDPRESS_APP_PASSWORD", "").strip()

    if not base_url:
        raise WordPressConfigError("Missing WORDPRESS_BASE_URL.")
    if not username:
        raise WordPressConfigError("Missing WORDPRESS_USERNAME.")
    if not app_password:
        raise WordPressConfigError("Missing WORDPRESS_APP_PASSWORD.")

    return base_url, username, app_password


def _build_payload(
    *,
    title: str,
    content: str,
    status: str,
    excerpt: str | None,
    slug: str | None,
    categories: list[int] | None,
    tags: list[int] | None,
    featured_media: int | None,
    publish_date_gmt: str | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "title": title,
        "content": content,
        "status": status,
    }

    if excerpt:
        payload["excerpt"] = excerpt
    if slug:
        payload["slug"] = slug
    if categories:
        payload["categories"] = categories
    if tags:
        payload["tags"] = tags
    if featured_media is not None:
        payload["featured_media"] = featured_media
    if publish_date_gmt:
        payload["date_gmt"] = publish_date_gmt

    return payload


async def publish_wordpress_article(
    *,
    title: str,
    content: str,
    post_id: int | None = None,
    status: str = "publish",
    excerpt: str | None = None,
    slug: str | None = None,
    categories: list[int] | None = None,
    tags: list[int] | None = None,
    featured_media: int | None = None,
    publish_date_gmt: str | None = None,
) -> str:
    """Create a WordPress post using basic authentication and app passwords."""
    base_url, username, app_password = _get_config()

    normalized_status = status.strip().lower()
    allowed_statuses = {"draft", "publish", "future", "pending", "private"}
    if normalized_status not in allowed_statuses:
        raise ValueError(f"status must be one of: {', '.join(sorted(allowed_statuses))}")

    payload = _build_payload(
        title=title,
        content=content,
        status=normalized_status,
        excerpt=excerpt,
        slug=slug,
        categories=categories,
        tags=tags,
        featured_media=featured_media,
        publish_date_gmt=publish_date_gmt,
    )

    endpoint = f"{base_url}/wp-json/wp/v2/posts"
    if post_id is not None:
        endpoint = f"{endpoint}/{post_id}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(endpoint, auth=(username, app_password), json=payload)

    if response.status_code >= 400:
        try:
            error_payload = response.json()
        except Exception:
            error_payload = {"message": response.text}
        message = error_payload.get("message", "Unknown WordPress error")
        raise WordPressPublishError(f"WordPress API error ({response.status_code}): {message}")

    data = response.json()
    post_id = data.get("id")
    post_status = data.get("status")
    post_link = data.get("link") or "(link unavailable)"

    return (
        "WordPress post created successfully.\n"
        f"- id: {post_id}\n"
        f"- status: {post_status}\n"
        f"- link: {post_link}"
    )


async def manage_wordpress_site(command: str) -> str:
    """Execute a wp-cli command over SSH."""
    import asyncio
    import shlex
    from app.core.config import get_credential
    
    ssh_target = get_credential("WORDPRESS_SSH_TARGET", "").strip()
    doc_root = get_credential("WORDPRESS_DOC_ROOT", "").strip()
    
    if not ssh_target:
        raise WordPressConfigError("Missing WORDPRESS_SSH_TARGET setting.")
    if not doc_root:
        raise WordPressConfigError("Missing WORDPRESS_DOC_ROOT setting.")
        
    # Support chained commands e.g. "theme install oceanwp && theme activate oceanwp"
    command_parts = [cmd.strip() for cmd in command.split("&&")]
    wp_commands = []
    for cmd in command_parts:
        if cmd.startswith("wp "):
            cmd = cmd[3:].strip()
        wp_commands.append(f"wp --path={shlex.quote(doc_root)} {cmd} --allow-root")
    
    final_command = " && ".join(wp_commands)

    ssh_cmd = [
        "ssh",
        "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=no",
        ssh_target,
        final_command
    ]
    
    process = await asyncio.create_subprocess_exec(
        *ssh_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    
    stdout, stderr = await process.communicate()
    
    output = []
    if stdout:
        output.append(stdout.decode().strip())
    if stderr:
        output.append(f"ERROR/WARNING: {stderr.decode().strip()}")
        
    if process.returncode != 0:
        raise WordPressPublishError(f"WP-CLI execution failed: {' | '.join(output)}")
        
    return "\n".join(output) or "Command executed successfully with no output."
