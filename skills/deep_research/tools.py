from app.services.tool_registry import ToolRegistry
from pydantic import BaseModel, Field
import asyncio
from duckduckgo_search import DDGS
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import httpx
import logging

logger = logging.getLogger(__name__)

# --- Schemas ---

class SearchSchema(BaseModel):
    query: str = Field(..., description="The query to search for on the web.")
    max_results: int = Field(5, description="Number of results to return.")

class BrowseSchema(BaseModel):
    url: str = Field(..., description="The URL to visit and read.")

# --- Implementations ---

async def web_search_impl(query: str, max_results: int = 5) -> str:
    """Searches the web using DuckDuckGo."""
    try:
        # DDGS is synchronous but fast enough, or we can wrap in executor
        loop = asyncio.get_event_loop()
        
        def _search():
            with DDGS() as ddgs:
                 # returns generator
                 return list(ddgs.text(query, max_results=max_results))
        
        results = await loop.run_in_executor(None, _search)
        
        if not results:
            return "No results found."
            
        formatted = ""
        for i, res in enumerate(results):
            formatted += f"### {i+1}. [{res.get('title')}]({res.get('href')})\n"
            formatted += f"{res.get('body')}\n\n"
            
        return formatted
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return f"Error searching web: {e}"

async def browse_page_impl(url: str) -> str:
    """Visits a page and extracts content using Playwright."""
    browser = None
    try:
        async with async_playwright() as p:
            # Launch browser (headless)
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
            page = await context.new_page()
            
            # Go to URL
            await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            
            # Get content
            html = await page.content()
            
            # Use BeautifulSoup to clean up
            soup = BeautifulSoup(html, "html.parser")
            
            # Remove scripts, styles
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.extract()
                
            text = soup.get_text(separator="\n")
            
            # Simple cleanup of whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            # Limit length to avoid context overflow (approx 10k chars check)
            if len(text) > 20000:
                text = text[:20000] + "\n...(truncated)"
                
            title = await page.title()
            return f"# Page Content: {title}\nURL: {url}\n\n{text}"
            
    except Exception as e:
        logger.error(f"Browse failed: {e}")
        return f"Error browsing page: {e}"
    finally:
        # Context manager handles browser close usually, but if we created it manually:
        pass

class ResearchTopicSchema(BaseModel):
    topic: str = Field(..., description="The topic to research deeply.")
    depth: int = Field(3, description="Number of pages to visit (max 5).")

async def research_topic_impl(topic: str, depth: int = 3) -> str:
    """Performs a multi-step research: Search -> Browse -> Synthesize."""
    if depth > 5: depth = 5
    
    # 1. Search
    search_results_markdown = await web_search_impl(topic, max_results=depth)
    
    # Extract URLs (naive regex)
    import re
    urls = re.findall(r'https?://[^\s\)]+', search_results_markdown)
    urls = [u.strip(")") for u in urls][:depth]
    
    if not urls:
        return f"Search found no accessible URLs. Search Results:\n{search_results_markdown}"

    # 2. Browse in parallel
    tasks = [browse_page_impl(url) for url in urls]
    pages_content = await asyncio.gather(*tasks)
    
    # 3. Combine
    combined = f"# Research Report: {topic}\n\n## Search Results\n{search_results_markdown}\n\n## Detailed Page Content\n"
    for i, content in enumerate(pages_content):
        combined += f"\n--- Source {i+1} ---\n{content}\n"
        
    return combined

# --- Registration ---

def register_tools(registry: ToolRegistry) -> None:
    registry.register(
        name="deep_research_search",
        description="Search the web for information using DuckDuckGo. Returns titles, links, and summaries.",
        args_schema=SearchSchema,
    )(web_search_impl)
    
    registry.register(
        name="deep_research_browse",
        description="Visit a specific URL and extract its text content using a headless browser. Use this to read articles, documentation, or gathered search links.",
        args_schema=BrowseSchema,
    )(browse_page_impl)

    registry.register(
        name="deep_research_topic",
        description="Perform a deep research on a topic. Searches for the topic, visits the top pages, and returns a combined report. Use this for broad queries.",
        args_schema=ResearchTopicSchema,
    )(research_topic_impl)
