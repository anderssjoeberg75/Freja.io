---
name: Deep Research
description: Provides capabilities to search the web and browse webpages using a headless browser.
---

# Deep Research Skill

This skill gives Freja access to the live internet.

## Tools

### `deep_research_search`
- **Description**: Search DuckDuckGo for a query.
- **Usage**: Use this to find initial information or links.

### `deep_research_browse`
- **Description**: Visit a specific URL and extract its content as Markdown.
- **Usage**: Use this to read the full content of a page found via search.

## Workflow
1.  Search for a topic: `deep_research_search(query="latest nvidia stock news")`
2.  Analyze results and pick relevant URLs.
3.  Browse a page: `deep_research_browse(url="...")`
4.  Synthesize findings.
