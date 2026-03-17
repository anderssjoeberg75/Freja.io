# WordPress Skill

This skill adds a `publish_wordpress_article` tool that creates posts on a WordPress site through the REST API.

## Required environment variables

- `WORDPRESS_BASE_URL`
- `WORDPRESS_USERNAME`
- `WORDPRESS_APP_PASSWORD`

## Example usage

- Save draft:
  - `status="draft"`
- Publish now:
  - `status="publish"`
- Schedule:
  - `status="future"`, `publish_date_gmt="2026-03-20T08:00:00"`

## Output

The tool returns the created post id, resulting status, and canonical link.
