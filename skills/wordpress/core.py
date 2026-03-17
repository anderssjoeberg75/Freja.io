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
    base_url = os.getenv("WORDPRESS_BASE_URL", "").strip().rstrip("/")
    username = os.getenv("WORDPRESS_USERNAME", "").strip()
    app_password = os.getenv("WORDPRESS_APP_PASSWORD", "").strip()

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
    status: str = "draft",
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
