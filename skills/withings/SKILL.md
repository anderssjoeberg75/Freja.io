---
name: Withings Health Integration
description: Provides access to Withings health data, including weight, body composition, and activity metrics.
---

# Withings Health Integration

This skill allows the assistant to retrieve health data from Withings devices (scales, sleep mats, etc.) via the Withings API.

## Capabilities

- **Get Health Report**: Retrieve the latest weight, body fat %, and other body composition metrics.
- **Get Activity**: (Planned) Retrieve activity data if available.

## Usage

The primary entry point is the `get_withings_health` tool.

### Example Queries
- "What is my latest weight?"
- "Check my body composition from Withings."
- "Show me my weight trend."

## Configuration

This skill requires OAuth2 authentication with Withings.
- **Client ID**: Configure in Settings.
- **Client Secret**: Configure in Settings.
- **Redirect URI**: Must be set to `<HOST>/api/integrations/withings/callback`.

## Files

- `tools.py`: Contains the `get_withings_health` tool implementation using the shared `WithingsTool`.
- `__init__.py`: Exports the tools for auto-discovery.

## Dependencies

- `skills/withings/core.py`: Shared logic for API communication.
- `app.core.dependencies`: Dependency injection for the tool instance.
