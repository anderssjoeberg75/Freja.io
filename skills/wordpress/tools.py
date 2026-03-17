"""WordPress tool registrations exposed by the WordPress skill."""

from app.services.tool_registry import ToolRegistry
from skills._core.definitions import PublishWordPressArticle


def register_tools(registry: ToolRegistry) -> None:
    """Register WordPress publishing tools in the shared tool registry."""

    @registry.register(
        name="publish_wordpress_article",
        description=(
            "Publishes or drafts an article in a WordPress blog via the REST API using "
            "application-password authentication."
        ),
        args_schema=PublishWordPressArticle,
    )
    async def publish_wordpress_article_impl(
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
        from skills.wordpress.core import (
            WordPressConfigError,
            WordPressPublishError,
            publish_wordpress_article,
        )

        try:
            return await publish_wordpress_article(
                title=title,
                content=content,
                status=status,
                excerpt=excerpt,
                slug=slug,
                categories=categories,
                tags=tags,
                featured_media=featured_media,
                publish_date_gmt=publish_date_gmt,
            )
        except WordPressConfigError as exc:
            return f"WordPress integration is not configured: {exc}"
        except WordPressPublishError as exc:
            return f"Failed to publish to WordPress: {exc}"
        except Exception as exc:
            return f"Unexpected WordPress publishing error: {exc}"
