"""Viral Hook Generator and Social Copy Intelligence Engine.

Provides 12 high-converting viral hook frameworks, audience/tone customization,
keyword extraction, and automated hashtag generation.
"""

from __future__ import annotations

import collections
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


# Common English stop words for clean keyword extraction
STOP_WORDS: Set[str] = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an",
    "and", "any", "are", "aren't", "as", "at", "be", "because", "been",
    "before", "being", "below", "between", "both", "but", "by", "can't",
    "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't",
    "doing", "don't", "down", "during", "each", "few", "for", "from",
    "further", "had", "hadn't", "has", "hasn't", "have", "haven't",
    "having", "he", "he'd", "he'll", "he's", "her", "here", "here's",
    "hers", "herself", "him", "himself", "his", "how", "how's", "i",
    "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't",
    "it", "it's", "its", "itself", "let's", "me", "more", "most",
    "mustn't", "my", "myself", "no", "nor", "not", "of", "off", "on",
    "once", "only", "or", "other", "ought", "our", "ours", "ourselves",
    "out", "over", "own", "same", "shan't", "she", "she'd", "she'll",
    "she's", "should", "shouldn't", "so", "some", "such", "than", "that",
    "that's", "the", "their", "theirs", "them", "themselves", "then",
    "there", "there's", "these", "they", "they'd", "they'll", "they're",
    "they've", "this", "those", "through", "to", "too", "under", "until",
    "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're",
    "we've", "were", "weren't", "what", "what's", "when", "when's",
    "where", "where's", "which", "while", "who", "who's", "whom",
    "why", "why's", "with", "won't", "would", "wouldn't", "you",
    "you'd", "you'll", "you're", "you've", "your", "yours", "yourself",
    "yourselves", "also", "just", "like", "will", "really", "get", "got",
    "use", "used", "make", "made", "one", "two", "see", "know", "think",
}


@dataclass
class HookTemplate:
    """Definition of a viral hook archetype."""

    template_id: int
    name: str
    category: str
    format_func: Callable[[str, Optional[str], str], str]
    base_virality_score: int
    description: str


class ViralHookGenerator:
    """12-Framework Viral Hook and Social Copy Generation Engine."""

    def __init__(self) -> None:
        """Initialize generator with 12 battle-tested viral hook templates."""
        self._templates: Dict[int, HookTemplate] = {}
        self._register_default_templates()

    def _register_default_templates(self) -> None:
        """Register the 12 core viral hook templates."""

        # 1. Contrarian / Hot Take
        def t1(topic: str, audience: Optional[str], tone: str) -> str:
            aud = f" for {audience}" if audience else ""
            if tone == "urgent":
                return f"Stop believing the hype: almost everything you've been told about {topic}{aud} is wrong.\n\nHere is the uncomfortable truth nobody admits:"
            elif tone == "casual":
                return f"Unpopular opinion: most advice on {topic}{aud} is pure noise.\n\nHere's what actually moves the needle:"
            return f"90% of people approach {topic}{aud} completely backwards.\n\nHere's the contrarian framework that actually works:"

        self._templates[1] = HookTemplate(
            template_id=1,
            name="Contrarian / Hot Take",
            category="Contrarian",
            format_func=t1,
            base_virality_score=94,
            description="Challenges conventional wisdom to immediately stop the scroll.",
        )

        # 2. Step-by-Step Blueprint
        def t2(topic: str, audience: Optional[str], tone: str) -> str:
            aud = f" for {audience}" if audience else ""
            if tone == "urgent":
                return f"The complete step-by-step blueprint to master {topic}{aud} in record time.\n\nFollow these 6 battle-tested steps:"
            elif tone == "casual":
                return f"I broke down {topic}{aud} into a simple step-by-step playbook.\n\nSteal this system (no fluff):"
            return f"The exact step-by-step blueprint to master {topic}{aud}.\n\nBookmark this 7-step roadmap:"

        self._templates[2] = HookTemplate(
            template_id=2,
            name="Step-by-Step Blueprint",
            category="Actionable Guide",
            format_func=t2,
            base_virality_score=91,
            description="Clear, linear process promise offering high utility.",
        )

        # 3. Data & Numbers
        def t3(topic: str, audience: Optional[str], tone: str) -> str:
            aud = f" among {audience}" if audience else ""
            if tone == "urgent":
                return f"We analyzed 1,500+ real data points on {topic}{aud}.\n\n93% fail. The top 7% share these 4 exact patterns:"
            elif tone == "casual":
                return f"I looked at 500+ examples of {topic}{aud}.\n\nThe data surprised me — here are the top 5 findings:"
            return f"After analyzing 1,000+ cases of {topic}{aud}, one pattern became clear:\n\nHere are the 5 surprising insights the numbers revealed:"

        self._templates[3] = HookTemplate(
            template_id=3,
            name="Data & Numbers",
            category="Data-Driven",
            format_func=t3,
            base_virality_score=96,
            description="Quantitative proof and statistics that command authority.",
        )

        # 4. Story / Experience
        def t4(topic: str, audience: Optional[str], tone: str) -> str:
            aud = f" (even for {audience})" if audience else ""
            if tone == "casual":
                return f"3 years ago, I had zero clue how to handle {topic}{aud}.\n\nToday it's my biggest unfair advantage. Here are the 5 lessons I wish I knew on Day 1:"
            elif tone == "urgent":
                return f"I spent 5 years making painful mistakes with {topic}{aud} so you don't have to.\n\nHere is the compressed playbook in 2 minutes:"
            return f"I spent over 500 hours dissecting {topic}{aud}.\n\nHere are the top 6 lessons that changed everything:"

        self._templates[4] = HookTemplate(
            template_id=4,
            name="Story / Experience",
            category="Narrative Journey",
            format_func=t4,
            base_virality_score=89,
            description="Relatable personal transformation that builds deep trust.",
        )

        # 5. Curated Resource / Tools List
        def t5(topic: str, audience: Optional[str], tone: str) -> str:
            aud = f" for {audience}" if audience else ""
            if tone == "casual":
                return f"10 free tools & resources for {topic}{aud} that feel illegal to know:\n\n(Save this before you lose it 🧵):"
            return f"The ultimate curated toolkit for {topic}{aud} (all free or cheap):\n\nHere are 8 resources that will save you 20+ hours a week:"

        self._templates[5] = HookTemplate(
            template_id=5,
            name="Curated Resource / Tools List",
            category="High-Utility Toolkit",
            format_func=t5,
            base_virality_score=95,
            description="Dense list of high-utility tools and assets designed for bookmarks.",
        )

        # 6. Before vs After
        def t6(topic: str, audience: Optional[str], tone: str) -> str:
            aud = f" ({audience} edition)" if audience else ""
            return f"Before vs After mastering {topic}{aud}:\n\n❌ Before: Overwhelmed, inconsistent, zero results\n✅ After: Automated, clear systems, 10x output\n\nHere is the exact shift that made the difference:"

        self._templates[6] = HookTemplate(
            template_id=6,
            name="Before vs After",
            category="Contrast Transformation",
            format_func=t6,
            base_virality_score=92,
            description="Visually striking contrast demonstrating immediate transformation.",
        )

        # 7. Question Hook
        def t7(topic: str, audience: Optional[str], tone: str) -> str:
            aud = f" for {audience}" if audience else ""
            if tone == "urgent":
                return f"Why are 99% of people still struggling with {topic}{aud} in 2025?\n\nIt comes down to 3 hidden bottlenecks:"
            return f"What if everything holding you back from winning at {topic}{aud} was just one flawed assumption?\n\nLet's break it down:"

        self._templates[7] = HookTemplate(
            template_id=7,
            name="Question Hook",
            category="Curiosity & Inquiry",
            format_func=t7,
            base_virality_score=88,
            description="Compelling open-ended inquiry triggering dopamine and curiosity.",
        )

        # 8. Mistake / Warning
        def t8(topic: str, audience: Optional[str], tone: str) -> str:
            aud = f" ({audience})" if audience else ""
            return f"Stop making these 5 costly mistakes with {topic}{aud}:\n\n(Number 3 quietly kills 80% of results):"

        self._templates[8] = HookTemplate(
            template_id=8,
            name="Mistake / Warning",
            category="Risk Mitigation",
            format_func=t8,
            base_virality_score=93,
            description="Loss aversion trigger warning readers of hidden pitfalls.",
        )

        # 9. Cheat Sheet
        def t9(topic: str, audience: Optional[str], tone: str) -> str:
            aud = f" for {audience}" if audience else ""
            return f"The 2-Minute {topic} Cheat Sheet{aud} (Bookmark for reference 📌):\n\nEverything you need to know on a single page:"

        self._templates[9] = HookTemplate(
            template_id=9,
            name="Cheat Sheet",
            category="Condensed Reference",
            format_func=t9,
            base_virality_score=97,
            description="Maximum density bookmark magnet delivering instant value.",
        )

        # 10. Framework Breakdown
        def t10(topic: str, audience: Optional[str], tone: str) -> str:
            aud = f" for {audience}" if audience else ""
            return f"The '3-Pillar Framework' top operators use to dominate {topic}{aud}:\n\nA breakdown of the mental model you can implement today:"

        self._templates[10] = HookTemplate(
            template_id=10,
            name="Framework Breakdown",
            category="Mental Model",
            format_func=t10,
            base_virality_score=90,
            description="Named proprietary framework that establishes thought leadership.",
        )

        # 11. Direct How-To
        def t11(topic: str, audience: Optional[str], tone: str) -> str:
            aud = f" for {audience}" if audience else ""
            return f"How to master {topic}{aud} in 15 minutes a day (without complex tools):\n\nA practical, no-BS guide:"

        self._templates[11] = HookTemplate(
            template_id=11,
            name="Direct How-To",
            category="Practical Instruction",
            format_func=t11,
            base_virality_score=87,
            description="Simple, direct promise answering how to achieve a desired outcome.",
        )

        # 12. Curiosity Gap
        def t12(topic: str, audience: Optional[str], tone: str) -> str:
            aud = f" regarding {audience}" if audience else ""
            return f"The hidden secret behind world-class {topic}{aud} that the top 1% never share publicly:\n\nHere is the inside breakdown:"

        self._templates[12] = HookTemplate(
            template_id=12,
            name="Curiosity Gap",
            category="Insider Secret",
            format_func=t12,
            base_virality_score=95,
            description="Creates an irresistible information gap that demands resolution.",
        )

    def register_custom_template(
        self,
        template_id: int,
        name: str,
        category: str,
        format_func: Callable[[str, Optional[str], str], str],
        base_virality_score: int = 90,
        description: str = "",
    ) -> None:
        """Register or override a hook template."""
        self._templates[template_id] = HookTemplate(
            template_id=template_id,
            name=name,
            category=category,
            format_func=format_func,
            base_virality_score=base_virality_score,
            description=description,
        )

    def get_template(self, template_id: int) -> Optional[HookTemplate]:
        """Get template definition by integer ID."""
        return self._templates.get(template_id)

    @classmethod
    def extract_keywords(
        cls,
        content: str,
        max_keywords: int = 10,
        min_length: int = 3,
    ) -> List[str]:
        """Extract high-relevance keywords and keyphrases from content.

        Performs stop-word filtering, word frequency scoring, and bigram collocation analysis.

        Args:
            content: Raw text or article body.
            max_keywords: Maximum number of keywords to return.
            min_length: Minimum character length for individual words.

        Returns:
            List of top extracted keywords sorted by importance.
        """
        if not content or not content.strip():
            return []

        # Tokenize words
        tokens = re.findall(r"\b[a-zA-Z][a-zA-Z0-9_\-]*\b", content.lower())
        meaningful_words = [
            t for t in tokens
            if len(t) >= min_length and t not in STOP_WORDS and not t.isdigit()
        ]

        if not meaningful_words:
            return []

        # Unigram frequency
        unigram_counts = collections.Counter(meaningful_words)

        # Bigram extraction (pairs of consecutive meaningful words)
        bigrams: List[str] = []
        for i in range(len(meaningful_words) - 1):
            w1, w2 = meaningful_words[i], meaningful_words[i + 1]
            if w1 != w2:
                bigrams.append(f"{w1} {w2}")
        bigram_counts = collections.Counter(bigrams)

        # Score candidates
        candidates: Dict[str, float] = {}
        for word, count in unigram_counts.items():
            # Frequency + small length bonus for substantive words
            candidates[word] = count * 1.0 + (len(word) * 0.05)

        for bigram, count in bigram_counts.items():
            if count >= 2:
                # Give higher weight to repeating compound phrases
                candidates[bigram] = count * 2.5

        sorted_candidates = sorted(
            candidates.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        return [word for word, _ in sorted_candidates[:max_keywords]]

    @classmethod
    def generate_hashtags(
        cls,
        topic: str,
        content: Optional[str] = None,
        count: int = 5,
        camel_case: bool = True,
    ) -> List[str]:
        """Generate formatted hashtags from a topic and optional body content.

        Args:
            topic: Primary topic string (e.g. 'Social Media Marketing').
            content: Optional body text to extract secondary tags from.
            count: Number of hashtags to produce.
            camel_case: Format as #SocialMedia (True) or #socialmedia (False).

        Returns:
            List of formatted hashtag strings including the leading #.
        """
        raw_tags: List[str] = []

        # 1. Add topic words
        topic_words = re.findall(r"\b[a-zA-Z0-9]+\b", topic)
        if len(topic_words) > 1:
            raw_tags.append("".join(w.capitalize() for w in topic_words))

        for w in topic_words:
            if len(w) >= 3 and w.lower() not in STOP_WORDS:
                raw_tags.append(w.capitalize())

        # 2. Add extracted keywords from content
        if content:
            keywords = cls.extract_keywords(content, max_keywords=count * 2)
            for kw in keywords:
                parts = kw.split()
                if len(parts) > 1:
                    raw_tags.append("".join(p.capitalize() for p in parts))
                else:
                    raw_tags.append(kw.capitalize())

        # Deduplicate while preserving order
        unique_tags: List[str] = []
        seen: Set[str] = set()
        for tag in raw_tags:
            norm = tag.lower()
            if norm not in seen and len(norm) >= 2:
                seen.add(norm)
                formatted_tag = tag if camel_case else norm
                unique_tags.append(f"#{formatted_tag}")
                if len(unique_tags) >= count:
                    break

        return unique_tags

    def generate_single_hook(
        self,
        template_id: int,
        topic: str,
        audience: Optional[str] = None,
        tone: str = "authoritative",
    ) -> Dict[str, Any]:
        """Generate a single viral hook by template ID with metadata."""
        tpl = self._templates.get(template_id)
        if not tpl:
            raise ValueError(f"Unknown template ID: {template_id}. Must be 1-12.")

        clean_topic = topic.strip()
        clean_audience = audience.strip() if audience else None
        norm_tone = tone.lower().strip()

        hook_text = tpl.format_func(clean_topic, clean_audience, norm_tone)
        hashtags = self.generate_hashtags(clean_topic, content=hook_text, count=3)

        # Tone adjustment on virality score
        score_adj = 0
        if norm_tone == "contrarian":
            score_adj += 2
        elif norm_tone == "urgent":
            score_adj += 1
        final_score = min(99, max(60, tpl.base_virality_score + score_adj))

        return {
            "template_id": tpl.template_id,
            "template_name": tpl.name,
            "category": tpl.category,
            "description": tpl.description,
            "hook_text": hook_text,
            "tone": norm_tone,
            "audience": clean_audience,
            "character_count": len(hook_text),
            "suggested_hashtags": hashtags,
            "estimated_virality_score": final_score,
            "follow_up_prompt": f"Continue thread explaining {clean_topic} with actionable takeaways.",
        }

    def generate_hooks(
        self,
        topic: str,
        audience: Optional[str] = None,
        tone: str = "authoritative",
    ) -> List[Dict[str, Any]]:
        """Generate all 12 viral hook variations for a topic and audience.

        Args:
            topic: The subject matter or core value proposition.
            audience: Optional target reader persona (e.g. 'Founders', 'Python Devs').
            tone: Voice styling ('authoritative', 'casual', 'urgent', 'contrarian', 'inspiring').

        Returns:
            List of 12 hook dictionaries with formatted text and virality metrics.
        """
        results: List[Dict[str, Any]] = []
        for template_id in sorted(self._templates.keys()):
            hook_data = self.generate_single_hook(
                template_id=template_id,
                topic=topic,
                audience=audience,
                tone=tone,
            )
            results.append(hook_data)
        return results
