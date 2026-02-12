import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Protocol, Tuple
from urllib.parse import quote_plus, urlparse

import httpx

from app.core.config import get_credential

logger = logging.getLogger(__name__)


# --- Data models ------------------------------------------------------------
# Shared response format for all search providers to keep integration simple.
@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str


# --- Provider interfaces ----------------------------------------------------
# Provider protocol allows swapping between Google CSE and SerpAPI.
class WebSearchProvider(Protocol):
    async def search(self, query: str, limit: int) -> List[SearchResult]:
        ...


# --- Simple in-memory TTL cache --------------------------------------------
# Cache external calls to reduce API costs and improve latency.
class TTLCache:
    def __init__(self):
        self._store: Dict[str, Tuple[float, object]] = {}

    def get(self, key: str):
        entry = self._store.get(key)
        if not entry:
            return None
        expires_at, value = entry
        if expires_at < time.time():
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: object, ttl_seconds: int):
        self._store[key] = (time.time() + ttl_seconds, value)


# --- HTTP helpers -----------------------------------------------------------
# Small retry helper with backoff for 429 rate-limit scenarios.
async def _request_json_with_backoff(client: httpx.AsyncClient, url: str, retries: int = 2) -> Dict:
    backoff_seconds = 1
    for attempt in range(retries + 1):
        response = await client.get(url, timeout=15.0)
        if response.status_code == 429 and attempt < retries:
            await asyncio.sleep(backoff_seconds)
            backoff_seconds *= 2
            continue
        response.raise_for_status()
        return response.json()
    return {}


# --- Search providers -------------------------------------------------------
class GoogleCSEProvider:
    async def search(self, query: str, limit: int) -> List[SearchResult]:
        api_key = get_credential("GOOGLE_CSE_API_KEY")
        cx = get_credential("GOOGLE_CSE_CX")
        if not api_key or not cx:
            raise RuntimeError("Google CSE credentials are missing")

        encoded_query = quote_plus(query)
        url = (
            "https://www.googleapis.com/customsearch/v1"
            f"?key={api_key}&cx={cx}&q={encoded_query}&num={max(1, min(limit, 10))}"
        )

        async with httpx.AsyncClient() as client:
            payload = await _request_json_with_backoff(client, url)

        items = payload.get("items", []) or []
        results: List[SearchResult] = []
        for item in items:
            results.append(
                SearchResult(
                    title=item.get("title", "Untitled"),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                )
            )
        return [result for result in results if result.url]


class SerpAPIProvider:
    async def search(self, query: str, limit: int) -> List[SearchResult]:
        api_key = get_credential("SERPAPI_API_KEY")
        if not api_key:
            raise RuntimeError("SerpAPI key is missing")

        encoded_query = quote_plus(query)
        url = (
            "https://serpapi.com/search.json"
            f"?engine=google&q={encoded_query}&num={max(1, min(limit, 10))}&api_key={api_key}"
        )

        async with httpx.AsyncClient() as client:
            payload = await _request_json_with_backoff(client, url)

        organic_results = payload.get("organic_results", []) or []
        results: List[SearchResult] = []
        for item in organic_results[:limit]:
            results.append(
                SearchResult(
                    title=item.get("title", "Untitled"),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                )
            )
        return [result for result in results if result.url]


class WikipediaProvider:
    async def search(self, query: str, limit: int, lang: str) -> List[SearchResult]:
        encoded_query = quote_plus(query)
        url = (
            f"https://{lang}.wikipedia.org/w/api.php"
            "?action=query&list=search&format=json"
            f"&srlimit={max(1, min(limit, 10))}&srsearch={encoded_query}"
        )

        async with httpx.AsyncClient() as client:
            payload = await _request_json_with_backoff(client, url)

        search_items = (payload.get("query") or {}).get("search", []) or []
        results: List[SearchResult] = []
        for item in search_items:
            title = item.get("title", "Untitled")
            snippet = (item.get("snippet", "") or "").replace("<span class=\"searchmatch\">", "").replace("</span>", "")
            page_url = f"https://{lang}.wikipedia.org/wiki/{title.replace(' ', '_')}"
            results.append(SearchResult(title=title, url=page_url, snippet=snippet))
        return results

    async def get_summary(self, title: str, lang: str) -> str:
        url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{quote_plus(title)}"
        async with httpx.AsyncClient() as client:
            payload = await _request_json_with_backoff(client, url)
        return payload.get("extract", "") or ""


# --- Decision gate ----------------------------------------------------------
# Deterministic fallback gate to avoid web calls unless the answer is uncertain.
def needs_web_fallback(answer_text: str, metadata: Optional[Dict] = None) -> bool:
    if not answer_text:
        return True

    lowered = answer_text.lower()
    uncertain_phrases = [
        "jag vet inte",
        "kan inte svara",
        "saknar information",
        "jag är osäker",
        "vet ej",
        "i don't know",
        "cannot answer",
        "not enough information",
        "uncertain",
    ]

    if any(phrase in lowered for phrase in uncertain_phrases):
        return True

    confidence = None
    if metadata:
        confidence = metadata.get("confidence")

    if confidence is None:
        return False

    try:
        return float(confidence) < 0.45
    except (TypeError, ValueError):
        return False


# --- Orchestrator -----------------------------------------------------------
# Coordinates providers, caching, deduplication and final response formatting.
class WebFallbackService:
    def __init__(self):
        self.cache = TTLCache()
        self.wikipedia = WikipediaProvider()

    def _get_search_provider(self) -> WebSearchProvider:
        provider_name = (get_credential("WEB_FALLBACK_PROVIDER", "google_cse") or "google_cse").lower()
        if provider_name == "serpapi":
            return SerpAPIProvider()
        return GoogleCSEProvider()

    async def build_fallback_answer(self, query: str, original_answer: str) -> str:
        max_sources = int(get_credential("WEB_FALLBACK_MAX_SOURCES", 5) or 5)
        wiki_lang = get_credential("WIKIPEDIA_LANG", "sv") or "sv"
        cache_ttl_minutes = int(get_credential("WEB_FALLBACK_CACHE_TTL_MINUTES", 20) or 20)

        web_cache_key = f"web:{query}:{max_sources}"
        wiki_cache_key = f"wiki:{query}:{max_sources}:{wiki_lang}"

        web_results = self.cache.get(web_cache_key)
        wiki_results = self.cache.get(wiki_cache_key)
        wiki_summary = self.cache.get(f"wiki_summary:{query}:{wiki_lang}")

        provider = self._get_search_provider()

        if web_results is None:
            try:
                web_results = await provider.search(query, max_sources)
                self.cache.set(web_cache_key, web_results, ttl_seconds=cache_ttl_minutes * 60)
            except Exception as exc:
                logger.warning(f"Web search failed: {exc}")
                web_results = []

        if wiki_results is None:
            try:
                wiki_results = await self.wikipedia.search(query, max_sources, wiki_lang)
                self.cache.set(wiki_cache_key, wiki_results, ttl_seconds=max(3600, cache_ttl_minutes * 60))
            except Exception as exc:
                logger.warning(f"Wikipedia search failed: {exc}")
                wiki_results = []

        if wiki_summary is None and wiki_results:
            try:
                wiki_summary = await self.wikipedia.get_summary(wiki_results[0].title, wiki_lang)
                self.cache.set(f"wiki_summary:{query}:{wiki_lang}", wiki_summary, ttl_seconds=max(3600, cache_ttl_minutes * 60))
            except Exception as exc:
                logger.warning(f"Wikipedia summary failed: {exc}")
                wiki_summary = ""

        if not web_results and not wiki_results:
            return f"{original_answer}\n\nJag kunde inte nå webben just nu."

        all_results = [*(web_results or []), *(wiki_results or [])]
        deduped_results = self._dedupe_results(all_results, max_sources)

        summary = self._build_swedish_summary(query=query, wiki_summary=wiki_summary or "", results=deduped_results)
        source_lines = "\n".join(f"- {item.url}" for item in deduped_results)

        return f"{summary}\n\nKällor:\n{source_lines}"

    def _dedupe_results(self, results: List[SearchResult], limit: int) -> List[SearchResult]:
        seen_urls = set()
        seen_domain_title = set()
        deduped: List[SearchResult] = []

        for result in results:
            clean_url = result.url.strip()
            if not clean_url or clean_url in seen_urls:
                continue

            domain = urlparse(clean_url).netloc.lower()
            domain_title_key = (domain, result.title.strip().lower())
            if domain_title_key in seen_domain_title:
                continue

            seen_urls.add(clean_url)
            seen_domain_title.add(domain_title_key)
            deduped.append(SearchResult(title=result.title, url=clean_url, snippet=result.snippet))

            if len(deduped) >= limit:
                break

        return deduped

    def _build_swedish_summary(self, query: str, wiki_summary: str, results: List[SearchResult]) -> str:
        snippets = [item.snippet.strip() for item in results if item.snippet.strip()]
        compact_snippets = snippets[:3]

        bullet_points = []
        for snippet in compact_snippets:
            bullet_points.append(f"- {snippet}")

        if wiki_summary:
            bullet_points.append(f"- Wikipedia: {wiki_summary[:320].strip()}")

        if not bullet_points:
            return f"Jag hittade källor om '{query}', men informationen var begränsad."

        summary_intro = f"Här är en kort sammanfattning om '{query}':"
        summary_body = "\n".join(bullet_points[:6])
        return f"{summary_intro}\n{summary_body}"
