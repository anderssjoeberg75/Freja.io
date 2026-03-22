"""WordPress tool registrations exposed by the WordPress skill."""

from app.services.tool_registry import ToolRegistry
from skills._core.definitions import PublishWordPressArticle, ManageWordPress


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
        post_id: int | None = None,
        status: str = "publish",
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
                post_id=post_id,
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


    @registry.register(
        name="manage_wordpress_site",
        description=(
            "Executes a wp-cli command over SSH to manage plugins, themes, updates, "
            "site health, or design/layout styling on the WordPress server. "
            "Use this tool exclusively for all WordPress structural and visual changes."
        ),
        args_schema=ManageWordPress,
    )
    async def manage_wordpress_site_impl(command: str) -> str:
        from skills.wordpress.core import (
            WordPressConfigError,
            WordPressPublishError,
            manage_wordpress_site,
        )

        try:
            return await manage_wordpress_site(command)
        except WordPressConfigError as exc:
            return f"WordPress SSH integration is not configured: {exc}"
        except WordPressPublishError as exc:
            return f"WordPress management failed: {exc}"
        except Exception as exc:
            return f"Unexpected WordPress SSH error: {exc}"
