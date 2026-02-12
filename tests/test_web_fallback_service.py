from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.web_fallback_service import SearchResult, needs_web_fallback, WebFallbackService


def test_needs_web_fallback_detects_uncertain_phrases():
    assert needs_web_fallback("Jag vet inte svaret på detta.") is True
    assert needs_web_fallback("I don't know enough facts.") is True


def test_needs_web_fallback_uses_confidence_metadata():
    assert needs_web_fallback("Här är ett svar.", {"confidence": 0.2}) is True
    assert needs_web_fallback("Här är ett svar.", {"confidence": 0.9}) is False


def test_dedupe_results_removes_duplicate_urls_and_domain_title_pairs():
    service = WebFallbackService()
    results = [
        SearchResult(title="Alpha", url="https://example.com/a", snippet="one"),
        SearchResult(title="Alpha", url="https://example.com/a", snippet="one duplicate"),
        SearchResult(title="Alpha", url="https://example.com/b", snippet="same domain and title"),
        SearchResult(title="Beta", url="https://example.com/c", snippet="different title"),
    ]

    deduped = service._dedupe_results(results, limit=5)

    assert [item.url for item in deduped] == [
        "https://example.com/a",
        "https://example.com/c",
    ]
