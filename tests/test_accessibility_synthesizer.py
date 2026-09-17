"""
Unit tests for AltTextSynthesizer, ContentWarningSuggestion, and accessibility evaluation suite.
"""

import pytest
from omnipost_social_engine.accessibility_synthesizer import (
    AltTextSynthesizer,
    AltTextEvaluation,
    ContentWarningSuggestion,
    evaluate_accessibility_suite,
    PLATFORM_ALT_LIMITS,
)


class TestAltTextSynthesizer:
    def test_clean_redundant_intro(self):
        cases = [
            ("Image of a golden retriever playing in grass.", "A golden retriever playing in grass."),
            ("Photo of the new MacBook Pro M4.", "The new MacBook Pro M4."),
            ("Picture of a sunset over the Pacific ocean.", "A sunset over the Pacific ocean."),
            ("Screenshot of terminal running pytest.", "Terminal running pytest."),
            ("A clean alt text without redundancy.", "A clean alt text without redundancy."),
        ]
        for raw, expected in cases:
            cleaned = AltTextSynthesizer.clean_redundant_intro(raw)
            assert cleaned == expected

    def test_evaluate_alt_text_empty(self):
        res = AltTextSynthesizer.evaluate_alt_text("", platform="twitter")
        assert res.descriptive_quality_score == 0
        assert res.grade == "FAIL"
        assert res.is_valid_length is False
        assert any("missing" in r.lower() for r in res.recommendations)

    def test_evaluate_alt_text_short(self):
        res = AltTextSynthesizer.evaluate_alt_text("Cute dog", platform="twitter")
        assert res.char_count == 8
        assert res.descriptive_quality_score < 70
        assert any("brief" in r.lower() for r in res.recommendations)

    def test_evaluate_alt_text_redundant_prefix(self):
        res = AltTextSynthesizer.evaluate_alt_text("Image of code editor with dark theme.", platform="mastodon")
        assert res.has_redundant_intro is True
        assert res.detected_redundancy is not None
        assert "image of" in res.detected_redundancy.lower()

    def test_evaluate_alt_text_high_quality(self):
        alt = "A high-contrast bar chart titled 'Quarterly Active Users' showing steady 25% growth from Q1 to Q4."
        res = AltTextSynthesizer.evaluate_alt_text(alt, platform="bluesky")
        assert res.descriptive_quality_score >= 85
        assert res.grade in ("AAA", "AA")
        assert res.is_valid_length is True
        assert res.has_redundant_intro is False

    def test_evaluate_alt_text_platform_limits(self):
        assert PLATFORM_ALT_LIMITS["mastodon"] == 1500
        assert PLATFORM_ALT_LIMITS["bluesky"] == 1000
        assert PLATFORM_ALT_LIMITS["twitter"] == 1000

        long_text = "A" * 1200 + "."
        eval_masto = AltTextSynthesizer.evaluate_alt_text(long_text, platform="mastodon")
        assert eval_masto.is_valid_length is True

        eval_twit = AltTextSynthesizer.evaluate_alt_text(long_text, platform="twitter")
        assert eval_twit.is_valid_length is False
        assert eval_twit.char_count == 1201


class TestContentWarningClassifier:
    def test_cw_spoilers(self):
        cw = AltTextSynthesizer.detect_content_warning("Massive spoiler! In the season finale, the main character returns.")
        assert cw.needs_cw is True
        assert "spoiler" in cw.categories_detected
        assert "Spoiler" in cw.suggested_warning_label
        assert "[CW: Spoiler]" in cw.formatted_mastodon_post

    def test_cw_politics(self):
        cw = AltTextSynthesizer.detect_content_warning("Breaking results from today's senate election ballot count.")
        assert cw.needs_cw is True
        assert "politics" in cw.categories_detected

    def test_cw_flashing_lights(self):
        cw = AltTextSynthesizer.detect_content_warning("Warning: Video contains strobe lights and rapid blinking effects.")
        assert cw.needs_cw is True
        assert "flashing_visuals" in cw.categories_detected

    def test_cw_clean_content(self):
        cw = AltTextSynthesizer.detect_content_warning("Just released a new Python package with zero dependencies!")
        assert cw.needs_cw is False
        assert cw.categories_detected == []
        assert cw.suggested_warning_label is None


class TestAccessibilitySuite:
    def test_evaluate_accessibility_suite(self):
        alt = "Picture of a laptop screen with Python code."
        post = "Huge plot twist in episode 10! Check this code snippet."
        suite = evaluate_accessibility_suite(alt_text=alt, post_text=post, platform="threads")

        assert suite["platform"] == "threads"
        assert "alt_evaluation" in suite
        assert suite["alt_evaluation"]["has_redundant_intro"] is True
        assert suite["cleaned_alt_text"] == "A laptop screen with Python code."
        assert suite["content_warning"]["needs_cw"] is True
        assert "spoiler" in suite["content_warning"]["categories_detected"]
