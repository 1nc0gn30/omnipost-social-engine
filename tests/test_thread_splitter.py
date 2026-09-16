"""Unit tests for thread_splitter.py (Thread splitting, numbering formats, markdown preservation)."""

import json
import pytest

from omnipost_social_engine.thread_splitter import (
    NumberingStyle,
    ThreadPost,
    ThreadSplitter,
)


def test_basic_thread_splitting():
    """Test splitting long content into multiple 280-char Twitter cards."""
    content = """
    Building high-performance distributed systems requires understanding network partitions.
    When a network partition occurs, you must choose between Consistency and Availability (CAP theorem).

    In modern cloud architectures, latency-sensitive applications often choose eventual consistency.
    This allows high write throughput across multiple geographic availability zones.

    To ensure data integrity, systems rely on vector clocks, CRDTs, or raft consensus groups.
    Each of these approaches comes with engineering trade-offs.

    Monitoring and distributed tracing (like OpenTelemetry) are essential for debugging partial failures.
    Without observability, diagnosing intermittent replication lag is nearly impossible.
    """
    splitter = ThreadSplitter(platform="twitter", numbering_style=NumberingStyle.SLASH_TOTAL)
    posts = splitter.split(content)

    assert len(posts) >= 2
    assert posts[0].index == 1
    assert posts[0].total == len(posts)

    for p in posts:
        assert p.char_count <= 280
        assert p.content.startswith(f"{p.index}/{p.total}")


def test_numbering_styles():
    """Verify different numbering styles (thread emoji, dot number, parentheses, emoji counter)."""
    text = "Paragraph one with some interesting insights.\n\nParagraph two with actionable takeaways."

    # Thread emoji
    s_emoji = ThreadSplitter(numbering_style=NumberingStyle.THREAD_EMOJI)
    posts_emoji = s_emoji.split(text)
    assert "🧵 1/" in posts_emoji[0].content

    # Dot number
    s_dot = ThreadSplitter(numbering_style=NumberingStyle.DOT_NUMBER)
    posts_dot = s_dot.split(text)
    assert posts_dot[0].content.startswith("1.")

    # Parentheses
    s_paren = ThreadSplitter(numbering_style=NumberingStyle.PARENTHESES)
    posts_paren = s_paren.split(text)
    assert posts_paren[0].content.startswith(f"(1/{len(posts_paren)})")

    # Suffix position
    s_suffix = ThreadSplitter(numbering_style=NumberingStyle.SLASH_TOTAL, numbering_position="suffix")
    posts_suffix = s_suffix.split(text)
    assert posts_suffix[0].content.endswith(f"1/{len(posts_suffix)}")


def test_custom_hook_and_cta():
    """Verify hook is placed on post 1 and CTA is attached to final post."""
    body = "Here is the main core tutorial text that provides deep value to the audience."
    custom_hook = "🔥 95% of engineers overlook this single architecture pattern:"
    custom_cta = "If you found this helpful, follow @alex for daily systems design tips! Repost to share."

    splitter = ThreadSplitter(platform="twitter")
    posts = splitter.split(body, hook=custom_hook, cta=custom_cta)

    assert len(posts) >= 1
    assert custom_hook in posts[0].content
    assert posts[0].is_hook is True

    last_post = posts[-1]
    assert custom_cta in last_post.content
    assert last_post.is_cta is True


def test_code_block_preservation():
    """Verify code blocks in markdown are preserved with backtick fences."""
    content = """
    Here is how you define a clean dataclass in Python:

    ```python
    from dataclasses import dataclass

    @dataclass
    class Node:
        id: str
        value: int
    ```

    Dataclasses automatically generate __init__, __repr__, and __eq__ methods.
    """
    splitter = ThreadSplitter(platform="twitter")
    posts = splitter.split(content)

    # Find the post with code
    code_posts = [p for p in posts if p.has_code]
    assert len(code_posts) >= 1
    assert "```python" in code_posts[0].content
    assert "class Node:" in code_posts[0].content


def test_markdown_quote_and_list_flags():
    """Test detection of quotes and bullet lists in thread cards."""
    content = """
    > "Simplicity is prerequisite for reliability." - Edsger W. Dijkstra

    Here are the key principles:
    - Keep dependencies minimal
    - Use strict type annotations
    - Write unit tests first
    """
    splitter = ThreadSplitter(platform="threads")
    posts = splitter.split(content)

    assert any(p.has_quote for p in posts)
    assert any(p.has_list for p in posts)


def test_preview_json_and_merge():
    """Test preview_thread, export_as_json, and merge_thread helpers."""
    content = "Card one information that is detailed.\n\nCard two information that contains extra context."
    splitter = ThreadSplitter(platform="bluesky", max_chars=45)
    posts = splitter.split(content)

    assert len(posts) >= 2

    # Preview
    preview = ThreadSplitter.preview_thread(posts)
    assert "Card 1/" in preview
    assert "Card 2/" in preview

    # JSON export
    json_str = ThreadSplitter.export_as_json(posts)
    parsed = json.loads(json_str)
    assert isinstance(parsed, list)
    assert len(parsed) == len(posts)
    assert parsed[0]["index"] == 1

    # Merge thread
    merged = ThreadSplitter.merge_thread(posts)
    assert "Card one information" in merged
    assert "Card two information" in merged


def test_empty_content_thread_splitting():
    """Verify empty or whitespace-only content produces empty thread."""
    splitter = ThreadSplitter(platform="twitter")
    assert splitter.split("") == []
    assert splitter.split("   \n\n   ") == []


def test_emoji_counter_numbering_style():
    """Verify NumberingStyle.EMOJI_COUNTER format."""
    content = "Point A.\n\nPoint B."
    splitter = ThreadSplitter(platform="twitter", numbering_style=NumberingStyle.EMOJI_COUNTER, max_chars=20)
    posts = splitter.split(content)

    assert len(posts) == 2
    assert "1️⃣" in posts[0].content
    assert "2️⃣" in posts[1].content

