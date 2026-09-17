"""Tests for optimal posting scheduler and hashtag analysis."""

from datetime import datetime
from omnipost_social_engine.schedule_planner import (
    HashtagAnalysisResult,
    PlatformPeakSlot,
    ScheduledPostSlot,
    analyze_hashtag_strategy,
    get_peak_engagement_matrix,
    plan_campaign_schedule,
)


def test_get_peak_engagement_matrix():
    slots = get_peak_engagement_matrix("linkedin")
    assert len(slots) > 0
    assert all(isinstance(s, PlatformPeakSlot) for s in slots)
    assert any(s.audience_persona == "B2B Morning Routine" for s in slots)
    assert any(s.start_hour == 7 for s in slots)


def test_plan_campaign_schedule():
    start = datetime(2026, 9, 22, 8, 0, 0)  # Tuesday 8:00 AM
    slots = plan_campaign_schedule(
        post_count=4,
        platforms=["twitter", "linkedin"],
        start_time=start,
        interval_hours=4,
    )
    assert len(slots) == 4
    assert slots[0].platform == "twitter"
    assert slots[0].projected_engagement_tier == "peak"
    assert slots[1].platform == "linkedin"
    assert slots[1].day_of_week == "Tuesday"
    assert slots[3].post_index == 4


def test_analyze_hashtag_strategy_twitter():
    content = "Just launched our new open source tool! #opensource #python #ai #datascience #machinelearning #dev"
    result = analyze_hashtag_strategy(content, "twitter")
    assert isinstance(result, HashtagAnalysisResult)
    assert len(result.extracted_tags) == 6
    assert not result.is_optimal_density  # Too many tags for Twitter
    assert "Too many hashtags" in result.feedback
    assert "#Opensource" in result.recommended_tags or "#OpenSource" in result.recommended_tags


def test_analyze_hashtag_strategy_optimal():
    content = "Building reliable LLM agent pipelines in production. #AI #Python"
    result = analyze_hashtag_strategy(content, "linkedin")
    assert result.is_optimal_density
    assert "Optimal" in result.feedback
    assert len(result.extracted_tags) == 2
