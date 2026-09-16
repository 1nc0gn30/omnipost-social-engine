"""Unit tests for hook_generator.py (12 viral hook templates, keywords, hashtags)."""

from typing import Any, Dict, List, Optional
import pytest

from omnipost_social_engine.hook_generator import (
    ViralHookGenerator,
)


def test_twelve_viral_hook_templates_generation():
    """Verify ViralHookGenerator produces all 12 distinct hook archetypes with metadata."""
    generator = ViralHookGenerator()
    hooks = generator.generate_hooks(
        topic="FastAPI Microservices",
        audience="Backend Engineers",
        tone="authoritative",
    )

    assert len(hooks) == 12

    expected_template_names = [
        "Contrarian / Hot Take",
        "Step-by-Step Blueprint",
        "Data & Numbers",
        "Story / Experience",
        "Curated Resource / Tools List",
        "Before vs After",
        "Question Hook",
        "Mistake / Warning",
        "Cheat Sheet",
        "Framework Breakdown",
        "Direct How-To",
        "Curiosity Gap",
    ]

    for idx, (hook_data, exp_name) in enumerate(zip(hooks, expected_template_names), start=1):
        assert hook_data["template_id"] == idx
        assert hook_data["template_name"] == exp_name
        assert "FastAPI Microservices" in hook_data["hook_text"]
        assert "Backend Engineers" in hook_data["hook_text"] or hook_data["audience"] == "Backend Engineers"
        assert len(hook_data["hook_text"]) == hook_data["character_count"]
        assert 60 <= hook_data["estimated_virality_score"] <= 100
        assert len(hook_data["suggested_hashtags"]) > 0
        assert len(hook_data["follow_up_prompt"]) > 0


def test_single_hook_generation():
    """Test generating a single hook by template ID."""
    generator = ViralHookGenerator()

    # Test template 1 (Contrarian)
    h1 = generator.generate_single_hook(1, "PostgreSQL Optimization", tone="urgent")
    assert h1["template_id"] == 1
    assert "PostgreSQL Optimization" in h1["hook_text"]
    assert h1["category"] == "Contrarian"

    # Test invalid template ID raises ValueError
    with pytest.raises(ValueError):
        generator.generate_single_hook(999, "Invalid")


def test_tones_customization():
    """Verify different tones alter the hook text."""
    generator = ViralHookGenerator()
    topic = "Async Programming"

    h_authoritative = generator.generate_single_hook(1, topic, tone="authoritative")
    h_urgent = generator.generate_single_hook(1, topic, tone="urgent")
    h_casual = generator.generate_single_hook(1, topic, tone="casual")

    assert h_authoritative["hook_text"] != h_urgent["hook_text"]
    assert h_urgent["hook_text"] != h_casual["hook_text"]


def test_keyword_extraction():
    """Test keyword and keyphrase extraction with stop-word filtering."""
    article = """
    Deploying high-concurrency microservices with Docker and Kubernetes provides incredible scalability.
    However, monitoring distributed systems and tracing network latency across services requires
    proper observability tools like Prometheus and Grafana. Kubernetes clusters need careful CPU limits.
    """
    keywords = ViralHookGenerator.extract_keywords(article, max_keywords=5, min_length=3)

    assert len(keywords) <= 5
    # Should include technical concepts, not stop words like 'and', 'the', 'with'
    assert not any(kw in ("and", "the", "with", "for", "however") for kw in keywords)
    assert any(term in keywords for term in ("kubernetes", "microservices", "distributed", "observability", "scalability", "services", "docker"))


def test_hashtag_generator():
    """Test hashtag generation and formatting (CamelCase vs lowercase)."""
    topic = "React Native Performance"
    content = "Optimizing mobile JavaScript rendering and bundle size for iOS and Android."

    tags_camel = ViralHookGenerator.generate_hashtags(topic, content=content, count=4, camel_case=True)
    tags_lower = ViralHookGenerator.generate_hashtags(topic, content=content, count=4, camel_case=False)

    assert len(tags_camel) == 4
    assert len(tags_lower) == 4

    assert all(t.startswith("#") for t in tags_camel)
    assert all(t.startswith("#") for t in tags_lower)
    assert any("ReactNative" in t or "React" in t for t in tags_camel)
    assert any("react" in t for t in tags_lower)


def test_custom_template_registration():
    """Test registering a custom hook template in ViralHookGenerator."""
    generator = ViralHookGenerator()

    def my_custom_format(topic: str, audience: Optional[str], tone: str) -> str:
        aud = f" for {audience}" if audience else ""
        return f"🚨 URGENT ALERT{aud}: Why you need to rethink {topic} today."

    generator.register_custom_template(
        template_id=13,
        name="Urgent Breaking Alert",
        category="News/Alert",
        format_func=my_custom_format,
        base_virality_score=98,
        description="Breaking news style urgency hook.",
    )

    custom_hook = generator.generate_single_hook(13, "AI Agents", audience="Product Managers")
    assert custom_hook["template_id"] == 13
    assert custom_hook["template_name"] == "Urgent Breaking Alert"
    assert "🚨 URGENT ALERT for Product Managers: Why you need to rethink AI Agents today." == custom_hook["hook_text"]


def test_keyword_extraction_empty_and_get_template():
    """Verify keyword extraction on empty string returns empty list, and get_template works."""
    assert ViralHookGenerator.extract_keywords("") == []
    assert ViralHookGenerator.extract_keywords("   ") == []

    generator = ViralHookGenerator()
    tpl = generator.get_template(1)
    assert tpl is not None
    assert tpl.template_id == 1
    assert generator.get_template(999) is None

