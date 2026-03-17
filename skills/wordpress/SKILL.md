---
name: wordpress-article-publisher
description: Use this skill when a user asks to create, draft, schedule, or publish a blog article on a WordPress site.
---

# WordPress Article Publisher

## Purpose
Create WordPress posts from chat content using the WordPress REST API.

## Configuration
Before using this skill, verify these environment variables:

- `WORDPRESS_BASE_URL` (example: `https://example.com`)
- `WORDPRESS_USERNAME` (WordPress user with post permissions)
- `WORDPRESS_APP_PASSWORD` (application password from user profile)

## Tool
- `publish_wordpress_article`

## Workflow
1. Draft the article content in clear Markdown or HTML.
2. Choose a safe default status:
   - `draft` for review-first flow.
   - `publish` for immediate publish.
   - `future` when `publish_date_gmt` is provided.
3. Call `publish_wordpress_article` with:
   - `title`
   - `content`
   - optional SEO/structure fields (`excerpt`, `slug`, `categories`, `tags`, `featured_media`, `publish_date_gmt`).
4. Confirm the returned post id, status, and link.
5. Keep the final user-facing response in Swedish.

## Notes
- `content` is sent as raw post content to `/wp-json/wp/v2/posts`.
- Category/tag values must be WordPress term IDs.
- Prefer creating drafts first when the user has not explicitly approved direct publishing.
