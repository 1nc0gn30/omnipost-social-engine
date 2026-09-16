"""Unit tests for formatter.py (Social media formatters, unicode stylers, engagement analyzer)."""

import pytest

from omnipost_social_engine.formatter import (
    EngagementReport,
    FormattedPost,
    SocialFormatter,
)


def test_url_hashtag_mention_extraction():
    """Verify URL, hashtag, and mention extraction."""
    sample = "Check out https://example.com/guide and http://sub.domain.org/path?q=1 #Python #AI_Tips @alice and @bob.dev!"
    urls = SocialFormatter.extract_urls(sample)
    hashtags = SocialFormatter.extract_hashtags(sample)
    mentions = SocialFormatter.extract_mentions(sample)

    assert "https://example.com/guide" in urls
    assert "http://sub.domain.org/path?q=1" in urls
    assert "Python" in hashtags
    assert "AI_Tips" in hashtags
    assert "alice" in mentions
    assert "bob.dev" in mentions


def test_unicode_styling_generators():
    """Test unicode bold, italic, and monospace font transformations."""
    text = "Hello World 123"
    bold = SocialFormatter.to_unicode_bold(text)
    italic = SocialFormatter.to_unicode_italic("Hello")
    mono = SocialFormatter.to_unicode_monospace("code123")

    assert bold != text
    assert "𝐇𝐞𝐥𝐥𝐨" in bold
    assert "𝟏𝟐𝟑" in bold
    assert "𝘏𝘦𝘭𝘭𝘰" in italic
    assert "𝚌𝚘𝚍𝚎" in mono


def test_markdown_unicode_styles():
    """Test automatic conversion of markdown syntax to unicode formatted text."""
    md_text = "This is **bold text** and this is *italic text* with `monospace code`!"
    converted = SocialFormatter.apply_markdown_unicode_styles(md_text)

    assert "**bold text**" not in converted
    assert "*italic text*" not in converted
    assert "`monospace code`" not in converted
    assert "𝐛𝐨𝐥𝐝" in converted
    assert "𝘪𝘵𝘢𝘭𝘪𝘤" in converted
    assert "𝚌𝚘𝚍𝚎" in converted


def test_grapheme_clustering_and_truncation():
    """Test grapheme cluster awareness with complex emojis, ZWJ sequences, and flags."""
    # US Flag: 2 regional indicators
    flag = "🇺🇸"
    assert SocialFormatter.calculate_grapheme_length(flag) == 1

    # Combining diacritics
    accented = "e\u0301"  # e with combining acute accent
    assert SocialFormatter.calculate_grapheme_length(accented) == 1

    # String truncation without breaking grapheme
    complex_text = "Hello 🚀 World 🇺🇸 Test string for truncation"
    truncated = SocialFormatter.truncate_grapheme_aware(complex_text, max_length=15, suffix="...")
    assert truncated.endswith("...")
    assert SocialFormatter.calculate_grapheme_length(truncated) <= 18


def test_twitter_formatting_and_tco_calculation():
    """Test Twitter length calculation with t.co URLs (23 chars) and emoji weighting."""
    # A long URL that is 80 characters long
    long_url = "https://example.com/very/long/url/that/would/normally/consume/eighty/characters/here"
    text_with_url = f"Announcing new release! {long_url} #Python"

    # In twitter, long_url counts as 23 chars
    # "Announcing new release! " (24) + URL (23) + " #Python" (8) = 55 chars
    calc_len = SocialFormatter.calculate_twitter_length(text_with_url)
    assert calc_len == 55

    # Test emoji weighted calculation (each emoji = 2 chars)
    emoji_text = "🚀🔥✨"
    assert SocialFormatter.calculate_twitter_length(emoji_text) == 6

    # Test formatting within limit
    res = SocialFormatter.format_twitter("Simple short tweet! 🚀")
    assert res.is_valid is True
    assert res.character_limit == 280
    assert res.platform == "twitter"

    # Test auto truncation
    long_tweet = "A" * 300
    res_trunc = SocialFormatter.format_twitter(long_tweet, auto_truncate=True)
    assert res_trunc.is_valid is True
    assert res_trunc.character_count <= 280
    assert res_trunc.content.endswith("...")


def test_linkedin_formatting():
    """Test LinkedIn 3000-char limit, whitespace hygiene, and optional unicode styling."""
    raw_linkedin = """
    First paragraph about leadership.
    
    
    
    Second paragraph after too many newlines.
    
    **Key Takeaway**: Always test your code.
    
    #Leadership #Tech #Dev
    """
    res = SocialFormatter.format_linkedin(raw_linkedin, apply_unicode_styling=True, consolidate_hashtags=True)
    assert res.is_valid is True
    assert res.character_limit == 3000
    assert "\n\n\n" not in res.content
    assert "𝐊𝐞𝐲" in res.content  # Unicode styled
    assert res.content.endswith("#Leadership #Tech #Dev")


def test_bluesky_formatting():
    """Test BlueSky 300-grapheme limit and truncation."""
    post_text = "Exploring the open social web on BlueSky! 🦋 " + ("Cool " * 70)
    res = SocialFormatter.format_bluesky(post_text, auto_truncate=False)
    assert res.is_valid is False
    assert len(res.warnings) > 0

    res_trunc = SocialFormatter.format_bluesky(post_text, auto_truncate=True)
    assert res_trunc.is_valid is True
    assert res_trunc.character_count <= 300


def test_threads_formatting():
    """Test Threads 500-char limit."""
    content = "Quick update for Threads community. " + ("Insightful comment. " * 15)
    res = SocialFormatter.format_threads(content)
    assert res.platform == "threads"
    assert res.character_limit == 500
    assert res.is_valid is True


def test_mastodon_formatting_with_cw():
    """Test Mastodon 500-char limit and Content Warning (CW) support."""
    # Test explicit content warning parameter
    res = SocialFormatter.format_mastodon("The murderer is the butler!", content_warning="Movie Spoilers")
    assert res.is_valid is True
    assert res.content_warning == "Movie Spoilers"
    assert res.character_count == len("The murderer is the butler!") + len("Movie Spoilers")

    # Test auto-detection of CW header in text
    cw_text = "CW: Politics and Election\n\nHere is my breakdown of the debate."
    res_detected = SocialFormatter.format_mastodon(cw_text)
    assert res_detected.content_warning == "Politics and Election"
    assert "Here is my breakdown of the debate." in res_detected.content


def test_reddit_formatting():
    """Test Reddit markdown formatting, title and body constraints."""
    title = "How we optimized our Python pipelines by 300%"
    body = "## Overview\nHere is the architecture:\n\n```python\nprint('fast')\n```\n\n> Quote from lead dev."
    res = SocialFormatter.format_reddit(body, title=title)

    assert res.is_valid is True
    assert res.title == title
    assert res.character_limit == 40000
    assert "## Overview" in res.content


def test_format_for_platform_dispatcher():
    """Test format_for_platform helper dispatcher."""
    p_tw = SocialFormatter.format_for_platform("twitter", "Hello Twitter")
    p_li = SocialFormatter.format_for_platform("linkedin", "Hello LinkedIn")
    p_bs = SocialFormatter.format_for_platform("bsky", "Hello BlueSky")
    p_th = SocialFormatter.format_for_platform("threads", "Hello Threads")
    p_ms = SocialFormatter.format_for_platform("mastodon", "Hello Mastodon")
    p_rd = SocialFormatter.format_for_platform("reddit", "Hello Reddit", title="Test Title")

    assert p_tw.platform == "twitter"
    assert p_li.platform == "linkedin"
    assert p_bs.platform == "bluesky"
    assert p_th.platform == "threads"
    assert p_ms.platform == "mastodon"
    assert p_rd.platform == "reddit"


def test_engagement_analyzer():
    """Test Engagement Score Analyzer calculation and suggestion generation."""
    high_engagement_post = """
    90% of developers approach SQL indexing completely backwards.

    Here are the 3 critical mistakes costing you 10x latency:

    1. Indexing low-cardinality columns
    2. Ignoring query execution plans
    3. Stacking unneeded composite indexes

    Which mistake have you seen most often? Let me know in the comments!

    #Database #Python #WebDev
    """
    report = SocialFormatter.analyze_engagement(high_engagement_post, platform="twitter")

    assert isinstance(report, EngagementReport)
    assert 70 <= report.score <= 100
    assert report.grade in ("A+", "A", "B")
    assert report.hook_score >= 15
    assert report.cta_score > 10
    assert report.whitespace_score > 10
    assert report.word_count > 20
    assert report.reading_time_seconds >= 1

    # Test empty text
    empty_report = SocialFormatter.analyze_engagement("")
    assert empty_report.score == 0
    assert empty_report.grade == "F"


def test_cjk_character_twitter_weighting():
    """Verify CJK wide characters receive weight 2 in Twitter calculations."""
    cjk_text = "你好世界"  # 4 CJK characters
    # 4 chars * 2 = 8 weight
    assert SocialFormatter.calculate_twitter_length(cjk_text) == 8


def test_formatted_post_and_engagement_report_to_dict():
    """Verify to_dict methods produce clean, serializable dictionaries."""
    post = SocialFormatter.format_twitter("Test tweet #OpenSource")
    p_dict = post.to_dict()
    assert isinstance(p_dict, dict)
    assert p_dict["platform"] == "twitter"
    assert "OpenSource" in p_dict["hashtags"]

    report = SocialFormatter.analyze_engagement("Why do 80% fail? Let me know! #Tech")
    r_dict = report.to_dict()
    assert isinstance(r_dict, dict)
    assert "score" in r_dict
    assert "breakdown" in r_dict
    assert "hook_score" in r_dict["breakdown"]

