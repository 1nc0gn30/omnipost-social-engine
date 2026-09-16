"""Social media content formatter, platform length engine, and engagement analyzer.

Supports Twitter/X (280 chars, t.co URL calculation, emoji weighting),
LinkedIn (3000 chars, unicode styling, whitespace hygiene),
BlueSky (300 chars, grapheme-aware truncation),
Threads (500 chars),
Mastodon (500 chars, Content Warning / CW support),
Reddit (Markdown formatting),
and Engagement Score Analysis (0-100).
"""

from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


# Regex patterns
URL_REGEX = re.compile(
    r"https?://(?:[a-zA-Z0-9\-._~:/?#\[\]@!$&'()*+,;=]|%[0-9a-fA-F]{2})+"
)
HASHTAG_REGEX = re.compile(r"(?<!\w)#([a-zA-Z0-9_\u0080-\uffff]+)")
MENTION_REGEX = re.compile(r"(?<!\w)@([a-zA-Z0-9_\.\-]+)")
EMOJI_REGEX = re.compile(
    r"[\U00010000-\U0010ffff]|[\u2600-\u27ff]|[\u2300-\u23ff]|[\u2b50-\u2b55]"
)

# Twitter constants
TWITTER_MAX_CHARS = 280
TWITTER_TCO_URL_LENGTH = 23

# Platform maximum character limits
PLATFORM_LIMITS = {
    "twitter": 280,
    "x": 280,
    "bluesky": 300,
    "bsky": 300,
    "threads": 500,
    "mastodon": 500,
    "linkedin": 3000,
    "reddit_title": 300,
    "reddit_body": 40000,
    "reddit": 40000,
}

# Unicode font tables for styling (LinkedIn, bio, etc.)
# Mathematical bold serif
BOLD_SERIF_MAP = {
    # Upper
    **{chr(ord("A") + i): chr(0x1D400 + i) for i in range(26)},
    # Lower
    **{chr(ord("a") + i): chr(0x1D41A + i) for i in range(26)},
    # Digits
    **{chr(ord("0") + i): chr(0x1D7CE + i) for i in range(10)},
}

# Mathematical sans-serif bold
BOLD_SANS_MAP = {
    **{chr(ord("A") + i): chr(0x1D5D4 + i) for i in range(26)},
    **{chr(ord("a") + i): chr(0x1D5EE + i) for i in range(26)},
    **{chr(ord("0") + i): chr(0x1D7EC + i) for i in range(10)},
}

# Mathematical italic (sans-serif italic for better rendering on mobile)
ITALIC_MAP = {
    **{chr(ord("A") + i): chr(0x1D608 + i) for i in range(26)},
    **{chr(ord("a") + i): chr(0x1D622 + i) for i in range(26)},
}

# Mathematical bold-italic
BOLD_ITALIC_MAP = {
    **{chr(ord("A") + i): chr(0x1D63C + i) for i in range(26)},
    **{chr(ord("a") + i): chr(0x1D656 + i) for i in range(26)},
}

# Mathematical monospace
MONOSPACE_MAP = {
    **{chr(ord("A") + i): chr(0x1D670 + i) for i in range(26)},
    **{chr(ord("a") + i): chr(0x1D68A + i) for i in range(26)},
    **{chr(ord("0") + i): chr(0x1D7F6 + i) for i in range(10)},
}


@dataclass
class FormattedPost:
    """Represents a formatted post ready for publication on a specific social platform."""

    platform: str
    content: str
    character_count: int
    character_limit: int
    is_valid: bool
    remaining_characters: int
    urls: List[str] = field(default_factory=list)
    hashtags: List[str] = field(default_factory=list)
    mentions: List[str] = field(default_factory=list)
    content_warning: Optional[str] = None
    title: Optional[str] = None
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert post to serializable dictionary."""
        return {
            "platform": self.platform,
            "content": self.content,
            "character_count": self.character_count,
            "character_limit": self.character_limit,
            "is_valid": self.is_valid,
            "remaining_characters": self.remaining_characters,
            "urls": self.urls,
            "hashtags": self.hashtags,
            "mentions": self.mentions,
            "content_warning": self.content_warning,
            "title": self.title,
            "warnings": self.warnings,
        }


@dataclass
class EngagementReport:
    """Detailed breakdown of engagement potential and content optimization."""

    score: int  # 0 to 100
    grade: str  # A+, A, B, C, D
    hook_score: float  # 0 to 25
    readability_score: float  # 0 to 25
    whitespace_score: float  # 0 to 20
    cta_score: float  # 0 to 15
    hashtag_score: float  # 0 to 15
    suggestions: List[str] = field(default_factory=list)
    word_count: int = 0
    reading_time_seconds: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "score": self.score,
            "grade": self.grade,
            "breakdown": {
                "hook_score": round(self.hook_score, 1),
                "readability_score": round(self.readability_score, 1),
                "whitespace_score": round(self.whitespace_score, 1),
                "cta_score": round(self.cta_score, 1),
                "hashtag_score": round(self.hashtag_score, 1),
            },
            "suggestions": self.suggestions,
            "word_count": self.word_count,
            "reading_time_seconds": self.reading_time_seconds,
        }


class SocialFormatter:
    """Enterprise multi-platform social media text formatter and analyzer."""

    @staticmethod
    def extract_urls(text: str) -> List[str]:
        """Extract all HTTP/HTTPS URLs from text."""
        return URL_REGEX.findall(text)

    @staticmethod
    def extract_hashtags(text: str) -> List[str]:
        """Extract all hashtag labels without the leading #."""
        return HASHTAG_REGEX.findall(text)

    @staticmethod
    def extract_mentions(text: str) -> List[str]:
        """Extract all handle mentions without the leading @."""
        return MENTION_REGEX.findall(text)

    @staticmethod
    def to_unicode_bold(text: str, sans_serif: bool = False) -> str:
        """Convert ASCII alphanumeric characters in text to Unicode bold characters.

        Example:
            'Hello 123' -> '𝐇𝐞𝐥𝐥𝐨 𝟏𝟐𝟑' or '𝗛𝗲𝗹𝗹𝗼 𝟭𝟮𝟯'
        """
        table = BOLD_SANS_MAP if sans_serif else BOLD_SERIF_MAP
        return "".join(table.get(char, char) for char in text)

    @staticmethod
    def to_unicode_italic(text: str) -> str:
        """Convert ASCII letters in text to Unicode mathematical italic characters.

        Example:
            'Hello' -> '𝘏𝘦𝘭𝘭𝘰'
        """
        return "".join(ITALIC_MAP.get(char, char) for char in text)

    @staticmethod
    def to_unicode_bold_italic(text: str) -> str:
        """Convert ASCII letters in text to Unicode bold-italic characters."""
        return "".join(BOLD_ITALIC_MAP.get(char, char) for char in text)

    @staticmethod
    def to_unicode_monospace(text: str) -> str:
        """Convert ASCII alphanumeric characters to Unicode monospace characters."""
        return "".join(MONOSPACE_MAP.get(char, char) for char in text)

    @classmethod
    def apply_markdown_unicode_styles(cls, text: str) -> str:
        """Convert standard markdown bold, italic, and code formatting to Unicode stylized text.

        - `***bold italic***` or `___bold italic___` -> Unicode bold-italic
        - `**bold**` or `__bold__` -> Unicode bold
        - `*italic*` or `_italic_` -> Unicode italic
        - `` `code` `` -> Unicode monospace
        """
        # Triple asterisks / underscores: bold-italic
        text = re.sub(
            r"(\*\*\*|___)(.+?)\1",
            lambda m: cls.to_unicode_bold_italic(m.group(2)),
            text,
        )
        # Double asterisks / underscores: bold
        text = re.sub(
            r"(\*\*|__)(.+?)\1",
            lambda m: cls.to_unicode_bold(m.group(2)),
            text,
        )
        # Single asterisks / underscores: italic (avoid matching within words like snake_case)
        text = re.sub(
            r"(?<!\w)(\*|_)(.+?)\1(?!\w)",
            lambda m: cls.to_unicode_italic(m.group(2)),
            text,
        )
        # Backtick code: monospace
        text = re.sub(
            r"`([^`]+)`",
            lambda m: cls.to_unicode_monospace(m.group(1)),
            text,
        )
        return text

    @staticmethod
    def get_grapheme_clusters(text: str) -> List[str]:
        """Segment a string into true Unicode grapheme clusters (pure Python stdlib).

        Handles combining characters, ZWJ sequences, skin tone modifiers,
        and regional indicator emoji pairs without corrupting characters.
        """
        if not text:
            return []

        clusters: List[str] = []
        current: List[str] = []
        in_zwj = False

        for char in text:
            cat = unicodedata.category(char)
            # Combining character categories (Mn: Nonspacing_Mark, Mc: Spacing_Combining_Mark, Me: Enclosing_Mark)
            is_combining = cat.startswith("M")
            is_variation = 0xFE00 <= ord(char) <= 0xFE0F or 0xE0100 <= ord(char) <= 0xE01EF
            is_skin_tone = 0x1F3FB <= ord(char) <= 0x1F3FF
            is_zwj = ord(char) == 0x200D

            if not current:
                current.append(char)
                in_zwj = is_zwj
                continue

            if is_combining or is_variation or is_skin_tone or in_zwj or is_zwj:
                current.append(char)
                in_zwj = is_zwj
            else:
                # Check for regional indicator pairs (e.g. Flags 🇺🇸)
                prev_char = current[-1]
                is_prev_reg_indicator = 0x1F1E6 <= ord(prev_char) <= 0x1F1FF
                is_curr_reg_indicator = 0x1F1E6 <= ord(char) <= 0x1F1FF

                if is_prev_reg_indicator and is_curr_reg_indicator and len(current) == 1:
                    current.append(char)
                    clusters.append("".join(current))
                    current = []
                else:
                    clusters.append("".join(current))
                    current = [char]
                in_zwj = False

        if current:
            clusters.append("".join(current))

        return clusters

    @classmethod
    def calculate_grapheme_length(cls, text: str) -> int:
        """Calculate the length of text in Unicode grapheme clusters."""
        return len(cls.get_grapheme_clusters(text))

    @classmethod
    def truncate_grapheme_aware(
        cls,
        text: str,
        max_length: int,
        suffix: str = "...",
    ) -> str:
        """Truncate text to max_length grapheme clusters without breaking emojis or combining characters."""
        clusters = cls.get_grapheme_clusters(text)
        if len(clusters) <= max_length:
            return text

        suffix_clusters = cls.get_grapheme_clusters(suffix)
        cutoff = max(0, max_length - len(suffix_clusters))
        truncated_text = "".join(clusters[:cutoff])

        # Try not to cut in the middle of a word if possible
        if " " in truncated_text:
            last_space = truncated_text.rfind(" ")
            if last_space > cutoff * 0.5:
                truncated_text = truncated_text[:last_space]

        return truncated_text.rstrip() + suffix

    @classmethod
    def calculate_twitter_length(cls, text: str) -> int:
        """Calculate the weighted character length of text using Twitter's counting algorithm.

        Rules:
        - Any URL (http/https) counts as 23 characters (t.co shortening).
        - Standard ASCII characters (0x0000 - 0x10FF) count as 1 character.
        - Non-ASCII, wide characters (CJK, fullwidth), and emojis count as 2 characters.
        """
        urls = cls.extract_urls(text)
        # Temporarily replace URLs with placeholder tokens
        scrubbed = text
        for url in urls:
            scrubbed = scrubbed.replace(url, "", 1)

        total_weight = len(urls) * TWITTER_TCO_URL_LENGTH

        for char in scrubbed:
            code = ord(char)
            # ASCII and basic Latin ranges count as 1 weight
            if code <= 0x10FF:
                total_weight += 1
            else:
                # Emojis, CJK, and wide unicode characters count as 2 weights
                east_asian = unicodedata.east_asian_width(char)
                if east_asian in ("W", "F") or code >= 0x1F000:
                    total_weight += 2
                else:
                    total_weight += 2

        return total_weight

    @classmethod
    def format_twitter(
        cls,
        text: str,
        auto_truncate: bool = False,
    ) -> FormattedPost:
        """Format and validate content for Twitter / X (280 weighted characters)."""
        clean_text = text.strip()
        weighted_len = cls.calculate_twitter_length(clean_text)
        limit = TWITTER_MAX_CHARS

        warnings: List[str] = []
        if weighted_len > limit:
            if auto_truncate:
                # Binary search or step truncate to fit twitter weighted length
                clusters = cls.get_grapheme_clusters(clean_text)
                while len(clusters) > 0 and cls.calculate_twitter_length("".join(clusters) + "...") > limit:
                    clusters.pop()
                clean_text = "".join(clusters).rstrip() + "..."
                weighted_len = cls.calculate_twitter_length(clean_text)
                warnings.append("Text was automatically truncated to fit Twitter 280-char limit.")
            else:
                warnings.append(
                    f"Post exceeds Twitter limit by {weighted_len - limit} weighted characters."
                )

        urls = cls.extract_urls(clean_text)
        hashtags = cls.extract_hashtags(clean_text)
        mentions = cls.extract_mentions(clean_text)

        return FormattedPost(
            platform="twitter",
            content=clean_text,
            character_count=weighted_len,
            character_limit=limit,
            is_valid=weighted_len <= limit,
            remaining_characters=limit - weighted_len,
            urls=urls,
            hashtags=hashtags,
            mentions=mentions,
            warnings=warnings,
        )

    @classmethod
    def format_linkedin(
        cls,
        text: str,
        apply_unicode_styling: bool = True,
        consolidate_hashtags: bool = False,
    ) -> FormattedPost:
        """Format content for LinkedIn (3000 chars, clean whitespace, optional unicode styling)."""
        limit = PLATFORM_LIMITS["linkedin"]
        clean_text = text.strip()

        if apply_unicode_styling:
            clean_text = cls.apply_markdown_unicode_styles(clean_text)

        # Normalize line breaks for LinkedIn readability: maximum 1 blank line between blocks
        paragraphs = [p.strip() for p in clean_text.split("\n") if p is not None]
        normalized_lines: List[str] = []
        empty_count = 0

        for line in paragraphs:
            if not line:
                empty_count += 1
                if empty_count <= 1:
                    normalized_lines.append("")
            else:
                empty_count = 0
                normalized_lines.append(line)

        clean_text = "\n".join(normalized_lines).strip()

        hashtags = cls.extract_hashtags(clean_text)
        if consolidate_hashtags and hashtags:
            # Strip inline hashtags and append cleanly to footer
            for tag in hashtags:
                clean_text = re.sub(r"#\b" + re.escape(tag) + r"\b", tag, clean_text)
            clean_text = clean_text.strip() + "\n\n" + " ".join(f"#{t}" for t in hashtags)

        char_count = len(clean_text)
        warnings: List[str] = []
        if char_count > limit:
            warnings.append(f"Post exceeds LinkedIn limit by {char_count - limit} characters.")

        return FormattedPost(
            platform="linkedin",
            content=clean_text,
            character_count=char_count,
            character_limit=limit,
            is_valid=char_count <= limit,
            remaining_characters=limit - char_count,
            urls=cls.extract_urls(clean_text),
            hashtags=hashtags,
            mentions=cls.extract_mentions(clean_text),
            warnings=warnings,
        )

    @classmethod
    def format_bluesky(
        cls,
        text: str,
        auto_truncate: bool = False,
    ) -> FormattedPost:
        """Format content for BlueSky (300 grapheme characters)."""
        limit = PLATFORM_LIMITS["bluesky"]
        clean_text = text.strip()
        grapheme_len = cls.calculate_grapheme_length(clean_text)

        warnings: List[str] = []
        if grapheme_len > limit:
            if auto_truncate:
                clean_text = cls.truncate_grapheme_aware(clean_text, limit, suffix="...")
                grapheme_len = cls.calculate_grapheme_length(clean_text)
                warnings.append("Text truncated to fit BlueSky 300-grapheme limit.")
            else:
                warnings.append(
                    f"Post exceeds BlueSky limit by {grapheme_len - limit} graphemes."
                )

        return FormattedPost(
            platform="bluesky",
            content=clean_text,
            character_count=grapheme_len,
            character_limit=limit,
            is_valid=grapheme_len <= limit,
            remaining_characters=limit - grapheme_len,
            urls=cls.extract_urls(clean_text),
            hashtags=cls.extract_hashtags(clean_text),
            mentions=cls.extract_mentions(clean_text),
            warnings=warnings,
        )

    @classmethod
    def format_threads(cls, text: str) -> FormattedPost:
        """Format content for Threads (500 characters)."""
        limit = PLATFORM_LIMITS["threads"]
        clean_text = text.strip()
        char_count = len(clean_text)

        warnings: List[str] = []
        if char_count > limit:
            warnings.append(f"Post exceeds Threads limit by {char_count - limit} characters.")

        return FormattedPost(
            platform="threads",
            content=clean_text,
            character_count=char_count,
            character_limit=limit,
            is_valid=char_count <= limit,
            remaining_characters=limit - char_count,
            urls=cls.extract_urls(clean_text),
            hashtags=cls.extract_hashtags(clean_text),
            mentions=cls.extract_mentions(clean_text),
            warnings=warnings,
        )

    @classmethod
    def format_mastodon(
        cls,
        text: str,
        content_warning: Optional[str] = None,
    ) -> FormattedPost:
        """Format content for Mastodon (500 characters, Content Warning / CW support)."""
        limit = PLATFORM_LIMITS["mastodon"]
        clean_text = text.strip()

        # Check if CW is embedded in text (e.g. 'CW: Spoiler content\n\nActual text' or '[cw: Spoilers]')
        cw = content_warning
        if not cw:
            cw_match = re.match(
                r"^(?:CW|cw|\[cw\]|\[CW\]):\s*([^\n]+)\n+(.*)$",
                clean_text,
                re.DOTALL,
            )
            if cw_match:
                cw = cw_match.group(1).strip()
                clean_text = cw_match.group(2).strip()

        # Mastodon character count includes both CW and main text
        total_len = len(clean_text) + (len(cw) if cw else 0)
        warnings: List[str] = []
        if total_len > limit:
            warnings.append(f"Post exceeds Mastodon limit by {total_len - limit} characters.")

        return FormattedPost(
            platform="mastodon",
            content=clean_text,
            character_count=total_len,
            character_limit=limit,
            is_valid=total_len <= limit,
            remaining_characters=limit - total_len,
            urls=cls.extract_urls(clean_text),
            hashtags=cls.extract_hashtags(clean_text),
            mentions=cls.extract_mentions(clean_text),
            content_warning=cw,
            warnings=warnings,
        )

    @classmethod
    def format_reddit(
        cls,
        text: str,
        title: Optional[str] = None,
    ) -> FormattedPost:
        """Format content for Reddit Markdown (300 char title, 40,000 char body)."""
        clean_title = title.strip() if title else None
        clean_body = text.strip()

        title_limit = PLATFORM_LIMITS["reddit_title"]
        body_limit = PLATFORM_LIMITS["reddit_body"]

        warnings: List[str] = []
        is_valid = True

        if clean_title and len(clean_title) > title_limit:
            is_valid = False
            warnings.append(
                f"Reddit title exceeds limit ({len(clean_title)}/{title_limit})."
            )

        if len(clean_body) > body_limit:
            is_valid = False
            warnings.append(
                f"Reddit body exceeds limit ({len(clean_body)}/{body_limit})."
            )

        return FormattedPost(
            platform="reddit",
            content=clean_body,
            character_count=len(clean_body),
            character_limit=body_limit,
            is_valid=is_valid,
            remaining_characters=body_limit - len(clean_body),
            urls=cls.extract_urls(clean_body),
            hashtags=cls.extract_hashtags(clean_body),
            mentions=cls.extract_mentions(clean_body),
            title=clean_title,
            warnings=warnings,
        )

    @classmethod
    def format_for_platform(
        cls,
        platform: str,
        text: str,
        **kwargs: Any,
    ) -> FormattedPost:
        """Format text for a given social platform by name."""
        norm = platform.lower().strip()
        if norm in ("twitter", "x"):
            return cls.format_twitter(text, **kwargs)
        elif norm in ("linkedin", "li"):
            return cls.format_linkedin(text, **kwargs)
        elif norm in ("bluesky", "bsky"):
            return cls.format_bluesky(text, **kwargs)
        elif norm == "threads":
            return cls.format_threads(text)
        elif norm in ("mastodon", "masto"):
            return cls.format_mastodon(text, **kwargs)
        elif norm == "reddit":
            return cls.format_reddit(text, **kwargs)
        else:
            # Fallback general formatter
            limit = kwargs.get("limit", 1000)
            clean = text.strip()
            return FormattedPost(
                platform=platform,
                content=clean,
                character_count=len(clean),
                character_limit=limit,
                is_valid=len(clean) <= limit,
                remaining_characters=limit - len(clean),
                urls=cls.extract_urls(clean),
                hashtags=cls.extract_hashtags(clean),
                mentions=cls.extract_mentions(clean),
            )

    @classmethod
    def analyze_engagement(
        cls,
        text: str,
        platform: str = "general",
    ) -> EngagementReport:
        """Analyze content and calculate an Engagement Score (0-100) with actionable suggestions.

        Criteria:
        1. Hook Strength (0-25 pts)
        2. Readability & Flow (0-25 pts)
        3. Line Break & White Space (0-20 pts)
        4. Call to Action (CTA) Presence (0-15 pts)
        5. Hashtag Strategy (0-15 pts)
        """
        if not text or not text.strip():
            return EngagementReport(
                score=0,
                grade="F",
                hook_score=0.0,
                readability_score=0.0,
                whitespace_score=0.0,
                cta_score=0.0,
                hashtag_score=0.0,
                suggestions=["Add substantive content to evaluate."],
            )

        clean_text = text.strip()
        lines = [line.strip() for line in clean_text.split("\n") if line.strip()]
        first_line = lines[0] if lines else ""
        first_two_lines = " ".join(lines[:2])
        words = re.findall(r"\b\w+\b", clean_text)
        word_count = len(words)

        suggestions: List[str] = []

        # 1. Hook Strength Score (0 to 25 pts)
        hook_score = 0.0
        # Check for numbers/stats in hook
        if re.search(r"\b\d+(?:[\.,]\d+)?%?|\$\d+|\b\d+\b", first_two_lines):
            hook_score += 7.0
        # Check for question format
        if "?" in first_two_lines:
            hook_score += 6.0
        # Check for high-converting trigger words
        trigger_words = {
            "secret", "blueprint", "framework", "mistake", "warning", "guide",
            "cheat sheet", "unpopular", "truth", "how to", "why", "stop",
            "never", "always", "surprising", "proven", "simple", "step", "rules",
            "lessons", "learned", "transformed", "overrated", "essential",
        }
        found_triggers = [
            t for t in trigger_words if t in first_two_lines.lower()
        ]
        if found_triggers:
            hook_score += min(8.0, len(found_triggers) * 4.0)
        # Check length of first line (punchy hooks: 20-90 chars)
        if 15 <= len(first_line) <= 100:
            hook_score += 4.0
        elif len(first_line) > 140:
            suggestions.append(
                "Make your opening hook punchier (aim for under 90 characters for maximum scroll-stopping impact)."
            )
        hook_score = min(25.0, hook_score)
        if hook_score < 12.0:
            suggestions.append(
                "Strengthen your hook: start with a provocative question, specific data/numbers, or a contrarian insight."
            )

        # 2. Readability & Sentence Length (0 to 25 pts)
        readability_score = 0.0
        sentences = [
            s.strip()
            for s in re.split(r"[.!?]+(?:\s+|\n+|$)", clean_text)
            if s.strip()
        ]
        num_sentences = max(1, len(sentences))
        avg_sentence_len = word_count / num_sentences

        # Ideal social sentence length is 6-16 words per sentence
        if 5 <= avg_sentence_len <= 16:
            readability_score += 20.0
        elif 16 < avg_sentence_len <= 24:
            readability_score += 14.0
        elif avg_sentence_len < 5:
            readability_score += 15.0
        else:
            readability_score += 6.0
            suggestions.append(
                f"Your sentences are relatively long (avg {avg_sentence_len:.1f} words). Break complex sentences into shorter, punchier lines."
            )

        # Variety and rhythm bonus
        if num_sentences >= 2:
            readability_score += 5.0
        readability_score = min(25.0, readability_score)

        # 3. Line Break & White Space (0 to 20 pts)
        whitespace_score = 0.0
        raw_lines = clean_text.split("\n")
        total_raw_lines = len(raw_lines)
        empty_lines = sum(1 for line in raw_lines if not line.strip())

        if total_raw_lines > 1:
            # Has line breaks
            whitespace_score += 10.0
            # Check for spaced paragraphs (blank lines)
            if empty_lines >= 1 or total_raw_lines >= 3:
                whitespace_score += 10.0
            else:
                whitespace_score += 5.0
                suggestions.append(
                    "Add blank lines between paragraphs to prevent dense walls of text."
                )
        else:
            if word_count > 30:
                suggestions.append(
                    "Format text with line breaks: wall of text severely reduces mobile engagement."
                )
            else:
                whitespace_score += 12.0  # Short one-liner is fine
        whitespace_score = min(20.0, whitespace_score)

        # 4. Call to Action (CTA) Score (0 to 15 pts)
        cta_score = 0.0
        cta_patterns = [
            r"\bfollow\b", r"\brepost\b", r"\bretweet\b", r"\bshare\b",
            r"\bcomment\b", r"\bbookmark\b", r"\bsave\b", r"\blink in\b",
            r"\bcheck out\b", r"\blet me know\b", r"\bwhat do you think\b",
            r"\byour thoughts\?", r"\breply\b", r"\bsubscribe\b", r"\bjoin\b",
            r"\bclick\b", r"\bdrop a\b", r"\bread more\b", r"\bgrab the\b",
        ]
        last_portion = " ".join(lines[-2:]).lower() if lines else clean_text.lower()
        cta_matched = any(re.search(pat, last_portion) for pat in cta_patterns)

        if cta_matched or "?" in last_portion:
            cta_score = 15.0
        else:
            cta_score = 4.0
            suggestions.append(
                "Add a closing Call-to-Action (CTA) prompting readers to reply, repost, save, or share their thoughts."
            )

        # 5. Hashtag Strategy (0 to 15 pts)
        hashtag_score = 0.0
        hashtags = cls.extract_hashtags(clean_text)
        tag_count = len(hashtags)

        if 1 <= tag_count <= 3:
            hashtag_score = 15.0
        elif 4 <= tag_count <= 5:
            hashtag_score = 10.0
        elif tag_count > 5:
            hashtag_score = 4.0
            suggestions.append(
                f"Too many hashtags ({tag_count}). Limit hashtags to 1-3 highly relevant tags to avoid algorithmic reach penalties."
            )
        else:
            # 0 hashtags: acceptable on Twitter/Threads, slightly sub-optimal on LinkedIn
            hashtag_score = 9.0
            if platform.lower() in ("linkedin", "general"):
                suggestions.append("Consider adding 1-3 targeted hashtags to increase discoverability.")

        total_score = int(
            round(
                hook_score
                + readability_score
                + whitespace_score
                + cta_score
                + hashtag_score
            )
        )
        total_score = max(0, min(100, total_score))

        # Grade calculation
        if total_score >= 92:
            grade = "A+"
        elif total_score >= 82:
            grade = "A"
        elif total_score >= 70:
            grade = "B"
        elif total_score >= 55:
            grade = "C"
        else:
            grade = "D"

        # Reading time estimate: approx 200 words per minute = ~3.3 words per second
        reading_time = max(1, int(math.ceil(word_count / 3.3)))

        return EngagementReport(
            score=total_score,
            grade=grade,
            hook_score=hook_score,
            readability_score=readability_score,
            whitespace_score=whitespace_score,
            cta_score=cta_score,
            hashtag_score=hashtag_score,
            suggestions=suggestions,
            word_count=word_count,
            reading_time_seconds=reading_time,
        )
