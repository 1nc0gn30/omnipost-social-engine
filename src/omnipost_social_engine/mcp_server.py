"""
Omnipost Social Engine - Model Context Protocol (MCP) Server
Stdio JSON-RPC 2.0 MCP server implementing social post formatting, thread splitting,
viral hook generation, engagement analysis, campaign exports, and multi-client configurations.
Zero external dependencies - pure Python stdlib.
"""

from __future__ import annotations

import json
import math
import os
import platform as sys_platform
import re
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from .campaign_exporter import PLATFORM_LIMITS, CampaignExporter
from .accessibility_synthesizer import evaluate_accessibility_suite


# Unicode Typography Mappings
UNICODE_MAPS: Dict[str, Dict[str, str]] = {
    "bold": {
        "A": "𝗔", "B": "𝗕", "C": "𝗖", "D": "𝗗", "E": "𝗘", "F": "𝗙", "G": "𝗚", "H": "𝗛",
        "I": "𝗜", "J": "𝗝", "K": "𝗞", "L": "𝗟", "M": "𝗠", "N": "𝗡", "O": "𝗢", "P": "𝗣",
        "Q": "𝗤", "R": "𝗥", "S": "𝗦", "T": "𝗧", "U": "𝗨", "V": "𝗩", "W": "𝗪", "X": "𝗫",
        "Y": "𝗬", "Z": "𝗭", "a": "𝗮", "b": "𝗯", "c": "𝗰", "d": "𝗱", "e": "𝗲", "f": "𝗳",
        "g": "𝗴", "h": "𝗵", "i": "𝗶", "j": "𝗷", "k": "𝗸", "l": "𝗹", "m": "𝗺", "n": "𝗻",
        "o": "𝗼", "p": "𝗽", "q": "𝗾", "r": "𝗿", "s": "𝘀", "t": "𝘁", "u": "𝘂", "v": "𝘃",
        "w": "𝘄", "x": "𝘅", "y": "𝘆", "z": "𝘇", "0": "𝟬", "1": "𝟭", "2": "𝟮", "3": "𝟯",
        "4": "𝟰", "5": "𝟱", "6": "𝟲", "7": "𝟳", "8": "𝟴", "9": "𝟵",
    },
    "italic": {
        "A": "𝘈", "B": "𝘉", "C": "𝘊", "D": "𝘋", "E": "𝘌", "F": "𝘍", "G": "𝘎", "H": "𝘏",
        "I": "𝘐", "J": "𝘑", "K": "𝘒", "L": "𝘓", "M": "𝘔", "N": "𝘕", "O": "𝘖", "P": "𝘗",
        "Q": "𝘘", "R": "𝘙", "S": "𝘚", "T": "𝘛", "U": "𝘜", "V": "𝘝", "W": "𝘞", "X": "𝘟",
        "Y": "𝘠", "Z": "𝘡", "a": "𝘢", "b": "𝘣", "c": "𝘤", "d": "𝘥", "e": "𝘦", "f": "𝘧",
        "g": "𝘨", "h": "𝘩", "i": "𝘪", "j": "𝘫", "k": "𝘬", "l": "𝘭", "m": "𝘮", "n": "𝘯",
        "o": "𝘰", "p": "𝘱", "q": "𝘲", "r": "𝘳", "s": "𝘴", "t": "𝘵", "u": "𝘶", "v": "𝘷",
        "w": "𝘸", "x": "𝘹", "y": "𝘺", "z": "𝘻",
    },
    "bold_italic": {
        "A": "𝘼", "B": "𝘽", "C": "𝘾", "D": "𝘿", "E": "𝙀", "F": "𝙁", "G": "𝙂", "H": "𝙃",
        "I": "𝙄", "J": "𝙅", "K": "𝙆", "L": "𝙇", "M": "𝙈", "N": "𝙉", "O": "𝙊", "P": "𝙋",
        "Q": "𝙌", "R": "𝙍", "S": "𝙎", "T": "𝙏", "U": "𝙐", "V": "𝙑", "W": "𝙒", "X": "𝙓",
        "Y": "𝙔", "Z": "𝙕", "a": "𝙖", "b": "𝙗", "c": "𝙘", "d": "𝙙", "e": "𝙚", "f": "𝙛",
        "g": "𝙜", "h": "𝙝", "i": "𝙞", "j": "𝙟", "k": "𝙠", "l": "𝙡", "m": "𝙢", "n": "𝙣",
        "o": "𝙤", "p": "𝙥", "q": "𝙦", "r": "𝙧", "s": "𝙨", "t": "𝙩", "u": "𝙪", "v": "𝙫",
        "w": "𝙬", "x": "𝙭", "y": "𝙮", "z": "𝙯",
    },
    "monospace": {
        "A": "𝙰", "B": "𝙱", "C": "𝙲", "D": "𝙳", "E": "𝙴", "F": "𝙵", "G": "𝙶", "H": "𝙷",
        "I": "𝙸", "J": "𝙹", "K": "𝙺", "L": "𝙻", "M": "𝙼", "N": "𝙽", "O": "𝙾", "P": "𝙿",
        "Q": "𝚀", "R": "𝚁", "S": "𝚂", "T": "𝚃", "U": "𝚄", "V": "𝚅", "W": "𝚆", "X": "𝚇",
        "Y": "𝚈", "Z": "𝚉", "a": "𝚊", "b": "𝚋", "c": "𝚌", "d": "𝚍", "e": "𝚎", "f": "𝚏",
        "g": "𝚐", "h": "𝚑", "i": "𝚒", "j": "𝚓", "k": "𝚔", "l": "𝚕", "m": "𝚖", "n": "𝚗",
        "o": "𝚘", "p": "𝚙", "q": "𝚚", "r": "𝚛", "s": "𝚜", "t": "𝚝", "u": "𝚞", "v": "𝚟",
        "w": "𝚠", "x": "𝚡", "y": "𝚢", "z": "𝚣", "0": "𝟶", "1": "𝟷", "2": "𝟸", "3": "𝟹",
        "4": "𝟺", "5": "𝟻", "6": "𝟼", "7": "𝟽", "8": "𝟾", "9": "𝟿",
    },
    "script": {
        "A": "𝒜", "B": "ℬ", "C": "𝒞", "D": "𝒟", "E": "ℰ", "F": "ℱ", "G": "𝒢", "H": "ℋ",
        "I": "ℐ", "J": "𝒥", "K": "𝒦", "L": "ℒ", "M": "ℳ", "N": "𝒩", "O": "𝒪", "P": "𝒫",
        "Q": "𝒬", "R": "ℛ", "S": "𝒮", "T": "𝒯", "U": "𝒰", "V": "𝒱", "W": "𝒲", "X": "𝒳",
        "Y": "𝒴", "Z": "𝒵", "a": "𝒶", "b": "𝒷", "c": "𝒸", "d": "𝒹", "e": "ℯ", "f": "𝒻",
        "g": "ℊ", "h": "𝒽", "i": "𝒾", "j": "𝒿", "k": "𝓀", "l": "𝓁", "m": "𝓂", "n": "𝓃",
        "o": "ℴ", "p": "𝓅", "q": "𝓆", "r": "𝓇", "s": "𝓈", "t": "𝓉", "u": "𝓊", "v": "𝓋",
        "w": "𝓌", "x": "𝓍", "y": "𝓎", "z": "𝓏",
    },
    "double_struck": {
        "A": "𝔸", "B": "𝔹", "C": "ℂ", "D": "𝔻", "E": "𝔼", "F": "𝔽", "G": "𝔾", "H": "ℍ",
        "I": "𝕀", "J": "𝕁", "K": "𝕂", "L": "𝕃", "M": "𝕄", "N": "ℕ", "O": "𝕆", "P": "ℙ",
        "Q": "ℚ", "R": "ℝ", "S": "𝕊", "T": "𝕋", "U": "𝕌", "V": "𝕍", "W": "𝕎", "X": "𝕏",
        "Y": "𝕐", "Z": "ℤ", "a": "𝕒", "b": "𝕓", "c": "𝕔", "d": "𝕕", "e": "𝕖", "f": "𝕗",
        "g": "𝕘", "h": "𝕙", "i": "𝕚", "j": "𝕛", "k": "𝕜", "l": "𝕝", "m": "𝕞", "n": "𝕟",
        "o": "𝕠", "p": "𝕡", "q": "𝕢", "r": "𝕣", "s": "𝕤", "t": "𝕥", "u": "𝕦", "v": "𝕧",
        "w": "𝕨", "x": "𝕩", "y": "𝕪", "z": "𝕫", "0": "𝟘", "1": "𝟙", "2": "𝟚", "3": "𝟛",
        "4": "𝟜", "5": "𝟝", "6": "𝟞", "7": "𝟟", "8": "𝟠", "9": "𝟡",
    },
    "sans": {
        "A": "𝖠", "B": "𝖡", "C": "𝖢", "D": "𝖣", "E": "𝖤", "F": "𝖥", "G": "𝖦", "H": "𝖧",
        "I": "𝖨", "J": "𝖩", "K": "𝖪", "L": "𝖫", "M": "𝖬", "N": "𝖭", "O": "𝖮", "P": "𝖯",
        "Q": "𝖰", "R": "𝖱", "S": "𝖲", "T": "𝖳", "U": "𝖴", "V": "𝖵", "W": "𝖶", "X": "𝖷",
        "Y": "𝖸", "Z": "𝖹", "a": "𝖺", "b": "𝖻", "c": "𝖼", "d": "𝖽", "e": "𝖾", "f": "𝖿",
        "g": "𝗀", "h": "𝗁", "i": "𝗂", "j": "𝗃", "k": "𝗄", "l": "𝗅", "m": "𝗆", "n": "𝗇",
        "o": "𝗈", "p": "𝗉", "q": "𝗊", "r": "𝗋", "s": "𝗌", "t": "𝗍", "u": "𝗎", "v": "𝗏",
        "w": "𝗐", "x": "𝗑", "y": "𝗒", "z": "𝗓", "0": "𝟢", "1": "𝟣", "2": "𝟤", "3": "𝟥",
        "4": "𝟦", "5": "𝟧", "6": "𝟨", "7": "𝟩", "8": "𝟪", "9": "𝟫",
    },
}


def apply_unicode_style(text: str, style: str) -> str:
    """Transform alphanumeric characters into styled Unicode typography."""
    style_key = style.lower().strip()
    if style_key in ("normal", "none", "plain", ""):
        return text

    if style_key == "underline":
        # Using combining low line \u0332
        return "".join(f"{c}\u0332" if c != "\n" else c for c in text)

    if style_key == "strikethrough":
        # Using combining long stroke overlay \u0336
        return "".join(f"{c}\u0336" if c != "\n" else c for c in text)

    mapping = UNICODE_MAPS.get(style_key)
    if not mapping:
        return text

    return "".join(mapping.get(c, c) for c in text)


def format_post_engine(
    text: str,
    platform: str = "twitter",
    style: str = "normal",
    hashtags: Optional[List[str]] = None,
    trim: bool = True,
) -> Dict[str, Any]:
    """Core post formatting engine."""
    plat = platform.lower().strip()
    plat_info = PLATFORM_LIMITS.get(plat, {"name": platform, "char_limit": 280})
    limit = plat_info["char_limit"]

    content = text.strip() if trim else text

    # Apply style if specified
    if style and style != "normal":
        content = apply_unicode_style(content, style)

    # Append hashtags if requested
    if hashtags:
        clean_tags = [f"#{h.lstrip('#')}" for h in hashtags if h.strip()]
        existing = set(re.findall(r"#\w+", content))
        tags_to_add = [t for t in clean_tags if t not in existing]
        if tags_to_add:
            content = f"{content}\n\n{' '.join(tags_to_add)}"

    char_count = len(content)
    word_count = len(content.split())
    is_valid = char_count <= limit
    remaining_chars = limit - char_count

    return {
        "text": content,
        "platform": plat,
        "platform_name": plat_info.get("name", plat),
        "char_count": char_count,
        "char_limit": limit,
        "remaining_chars": remaining_chars,
        "is_valid": is_valid,
        "word_count": word_count,
        "style": style,
    }


def split_thread_engine(
    text: str,
    limit: int = 280,
    platform: str = "twitter",
    numbering: bool = True,
    numbering_format: str = "fraction",
) -> Dict[str, Any]:
    """Split long copy into optimal thread segments."""
    plat = platform.lower().strip()
    if limit <= 0:
        limit = PLATFORM_LIMITS.get(plat, {}).get("char_limit", 280)

    # Clean input paragraphs
    raw_paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not raw_paragraphs:
        raw_paragraphs = [text.strip()] if text.strip() else [""]

    # Initial chunking
    chunks: List[str] = []
    current_chunk: List[str] = []
    current_len = 0

    # Reserve characters for thread numbering like " (12/12)" ~ 9 chars
    reserve_chars = 12 if numbering else 0
    effective_limit = max(10, limit - reserve_chars)

    for para in raw_paragraphs:
        if len(para) <= effective_limit:
            # Check if adding this paragraph exceeds current chunk
            added_len = len(para) + (2 if current_chunk else 0)
            if current_len + added_len <= effective_limit:
                current_chunk.append(para)
                current_len += added_len
            else:
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                current_chunk = [para]
                current_len = len(para)
        else:
            # Sentence level splitting
            if current_chunk:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = []
                current_len = 0

            sentences = re.split(r"(?<=[.!?])\s+", para)
            sub_chunk: List[str] = []
            sub_len = 0
            for sent in sentences:
                sent = sent.strip()
                if not sent:
                    continue
                if len(sent) > effective_limit:
                    # Word level splitting
                    if sub_chunk:
                        chunks.append(" ".join(sub_chunk))
                        sub_chunk = []
                        sub_len = 0
                    words = sent.split()
                    word_sub: List[str] = []
                    word_len = 0
                    for w in words:
                        if word_len + len(w) + 1 <= effective_limit:
                            word_sub.append(w)
                            word_len += len(w) + 1
                        else:
                            if word_sub:
                                chunks.append(" ".join(word_sub))
                            word_sub = [w]
                            word_len = len(w)
                    if word_sub:
                        chunks.append(" ".join(word_sub))
                else:
                    if sub_len + len(sent) + 1 <= effective_limit:
                        sub_chunk.append(sent)
                        sub_len += len(sent) + 1
                    else:
                        chunks.append(" ".join(sub_chunk))
                        sub_chunk = [sent]
                        sub_len = len(sent)
            if sub_chunk:
                chunks.append(" ".join(sub_chunk))

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    if not chunks:
        chunks = [""]

    total = len(chunks)
    posts: List[Dict[str, Any]] = []

    for idx, chunk in enumerate(chunks, 1):
        formatted_chunk = chunk
        if numbering and total > 1:
            if numbering_format == "fraction_thread":
                prefix = f"🧵 {idx}/{total}\n\n" if idx == 1 else f"{idx}/{total}\n\n"
                formatted_chunk = f"{prefix}{chunk}"
            elif numbering_format == "bracket":
                formatted_chunk = f"{chunk}\n\n[{idx}/{total}]"
            elif numbering_format == "counter":
                formatted_chunk = f"{idx}. {chunk}"
            else:  # fraction default
                formatted_chunk = f"{chunk}\n\n({idx}/{total})"

        posts.append({
            "index": idx,
            "total": total,
            "content": formatted_chunk,
            "char_count": len(formatted_chunk),
            "char_limit": limit,
            "is_valid": len(formatted_chunk) <= limit,
        })

    return {
        "platform": plat,
        "total_posts": len(posts),
        "char_limit": limit,
        "posts": posts,
    }


def generate_hooks_engine(
    topic: str,
    niche: str = "tech",
    framework: str = "all",
    count: int = 10,
) -> Dict[str, Any]:
    """Generate viral headlines and opening hooks."""
    clean_topic = topic.strip()
    clean_niche = niche.strip()
    fw = framework.lower().strip()

    templates: List[Tuple[str, str]] = [
        # (framework_id, template_str)
        ("contrarian", "Most people think {topic} is about X. They're completely wrong.\n\nHere is the truth:"),
        ("contrarian", "Unpopular opinion: 90% of advice on {topic} is outdated.\n\nHere is what actually works in 2026:"),
        ("contrarian", "Stop doing {topic} the hard way.\n\nHere is the exact shortcut top performers use:"),
        
        ("question", "Why is almost nobody talking about this {topic} breakthrough?"),
        ("question", "What happens when you apply {topic} to your daily workflow for 30 days?"),
        ("question", "Is {topic} the most underrated skill in {niche}? (Data says yes)"),

        ("number_list", "7 brutal truths about {topic} I wish I knew 5 years ago:"),
        ("number_list", "10 micro-habits for {topic} that generate 10x ROI:"),
        ("number_list", "5 simple tools that will automate 80% of your {topic} workflow:"),

        ("curiosity_gap", "This 1 subtle mindset shift in {topic} changed my entire career:"),
        ("curiosity_gap", "The biggest secret about {topic} nobody will tell you for free:"),
        ("curiosity_gap", "I analyzed 1,000 top examples of {topic}. Here is the 1 pattern they all share:"),

        ("transformation", "How I went from struggling with {topic} to top 1% in 60 days:"),
        ("transformation", "From 0 to mastery in {topic}: The exact step-by-step roadmap:"),
        ("transformation", "How to 10x your results with {topic} without spending a dollar:"),

        ("how_to", "How to master {topic} in 2026 (even if you are starting from zero):"),
        ("how_to", "The complete beginner's cheat sheet for {topic}:"),
        ("how_to", "A step-by-step masterclass on {topic} in 5 minutes:"),

        ("negative_bias", "5 deadly mistakes destroying your results with {topic}:"),
        ("negative_bias", "If you are making this 1 mistake with {topic}, stop immediately:"),
        ("negative_bias", "Why 99% of people fail at {topic} (and how to be the 1% who win):"),

        ("secret_mistake", "The {topic} blueprint that top {niche} leaders keep behind closed doors:"),
        ("secret_mistake", "Steal my 4-step framework for {topic} (took me 3 years to build):"),

        ("story_lead", "Last week, I ran a radical experiment on {topic}. Here is what happened:"),
        ("story_lead", "I spent 40 hours testing every {topic} method so you don't have to:"),
    ]

    filtered_templates = templates
    if fw != "all":
        filtered_templates = [t for t in templates if t[0] == fw]
        if not filtered_templates:
            filtered_templates = templates

    generated: List[Dict[str, Any]] = []
    # Loop over templates and format
    for idx, (f_type, tpl) in enumerate(filtered_templates, 1):
        hook_text = tpl.format(topic=clean_topic, niche=clean_niche)
        generated.append({
            "id": idx,
            "framework": f_type,
            "hook": hook_text,
            "char_count": len(hook_text),
        })
        if len(generated) >= count:
            break

    # If count requested is larger than template pool, cycle with slight variations
    if len(generated) < count:
        idx = len(generated) + 1
        for f_type, tpl in filtered_templates:
            hook_text = f"🔥 {tpl.format(topic=clean_topic, niche=clean_niche)}"
            generated.append({
                "id": idx,
                "framework": f_type,
                "hook": hook_text,
                "char_count": len(hook_text),
            })
            idx += 1
            if len(generated) >= count:
                break

    return {
        "topic": clean_topic,
        "niche": clean_niche,
        "framework": fw,
        "count": len(generated),
        "hooks": generated[:count],
    }


def analyze_engagement_engine(text: str, platform: str = "twitter") -> Dict[str, Any]:
    """
    Computes a 0-100 viral readiness score, readability grade, structure breakdown,
    sentiment/urgency indicators, and actionable optimization advice.
    """
    content = text.strip()
    plat = platform.lower().strip()
    plat_info = PLATFORM_LIMITS.get(plat, {"char_limit": 280})
    limit = plat_info["char_limit"]

    char_count = len(content)
    words = content.split()
    word_count = len(words)
    lines = [l for l in content.split("\n") if l.strip()]
    line_count = len(lines)

    if word_count == 0:
        return {
            "score": 0,
            "grade": "F",
            "viral_readiness": "Poor",
            "metrics": {"char_count": 0, "word_count": 0, "line_count": 0},
            "recommendations": ["Add content to begin analysis."],
        }

    # Sentence count
    sentences = [s for s in re.split(r"[.!?]+", content) if s.strip()]
    sentence_count = max(1, len(sentences))

    # Syllable approximation
    def count_syllables(word: str) -> int:
        w = word.lower().strip(".:;?!\"'()")
        if not w:
            return 1
        syls = len(re.findall(r"[aeiouy]+", w))
        if w.endswith("e") and not w.endswith("le") and syls > 1:
            syls -= 1
        return max(1, syls)

    total_syllables = sum(count_syllables(w) for w in words)
    avg_sentence_len = word_count / sentence_count
    avg_syllables_per_word = total_syllables / word_count

    # Flesch Reading Ease
    flesch_score = 206.835 - (1.015 * avg_sentence_len) - (84.6 * avg_syllables_per_word)
    flesch_score = max(0, min(100, flesch_score))

    # Flesch-Kincaid Grade Level
    fk_grade = (0.39 * avg_sentence_len) + (11.8 * avg_syllables_per_word) - 15.59
    fk_grade = max(1.0, min(18.0, fk_grade))

    # Hook Strength Evaluation (first sentence / first line)
    first_line = lines[0] if lines else ""
    hook_score = 10
    hook_tips: List[str] = []

    # Power / curiosity words
    power_words = {
        "secret", "truth", "proven", "mistake", "hack", "blueprint", "master",
        "steal", "framework", "unpopular", "cheat", "brutal", "insider", "roadmap",
        "automates", "nobody", "stop", "why", "how", "fast", "simple", "breakthrough",
        "most", "completely", "wrong", "favorite"
    }
    found_power = [w.lower() for w in re.findall(r"\b\w+\b", first_line) if w.lower() in power_words]
    if found_power:
        hook_score += min(15, len(found_power) * 8)

    # Question or curiosity trigger
    if "?" in first_line:
        hook_score += 10

    # Numbers in hook
    if re.search(r"\b\d+\b", first_line):
        hook_score += 10

    # Short & punchy first line
    if len(first_line.split()) <= 15:
        hook_score += 10
    elif len(first_line.split()) > 25:
        hook_score -= 5
        hook_tips.append("Shorten your opening line to under 15 words for higher mobile retention.")

    hook_score = max(10, min(35, hook_score))

    # Formatting & Scannability Score
    formatting_score = 10
    # Has empty line spacing
    if "\n\n" in content:
        formatting_score += 10
    else:
        hook_tips.append("Add double line breaks between ideas for mobile skimmability.")

    # Bullet / list markers
    has_bullets = bool(re.search(r"^[\d\-\*•✓\>]\s+", content, re.MULTILINE))
    if has_bullets:
        formatting_score += 10

    # Emojis count (1-4 is sweet spot)
    emojis = re.findall(r"[\U00010000-\U0010ffff]", content)
    emoji_count = len(emojis)
    if 1 <= emoji_count <= 5:
        formatting_score += 5
    elif emoji_count > 8:
        formatting_score -= 5
        hook_tips.append("Reduce emoji clutter (keep between 1 and 4 emojis).")

    formatting_score = max(10, min(30, formatting_score))

    # Call to Action (CTA) & Engagement Triggers
    cta_score = 5
    cta_patterns = [
        r"\b(comment|reply|share|repost|rt|bookmark|save|follow|check out|link|click|thoughts|agree|let me know|drop)\b",
        r"\b(what is|what are|👇|🧵|\?)\b",
    ]
    has_cta = any(re.search(p, content, re.IGNORECASE) for p in cta_patterns)
    if has_cta:
        cta_score = 20
    else:
        hook_tips.append("Add a clear Call-To-Action (e.g. 'What are your thoughts? Reply below 👇').")

    # Readability score contribution (up to 15)
    readability_contrib = round((flesch_score / 100) * 15, 1)

    # Platform compliance & character length optimization
    length_penalty = 0
    if char_count > limit:
        # Check how much it exceeds
        excess = char_count - limit
        if excess > limit * 0.5:
            length_penalty = 25
        elif excess > limit * 0.2:
            length_penalty = 15
        else:
            length_penalty = 8
        hook_tips.append(f"Content exceeds {plat} limit by {excess} chars ({char_count}/{limit}). Split into thread.")

    # Overall Score Calculation
    raw_total = hook_score + formatting_score + cta_score + readability_contrib - length_penalty
    final_score = int(max(5, min(100, round(raw_total))))

    if final_score >= 85:
        grade = "A+"
        readiness = "Viral Ready"
    elif final_score >= 75:
        grade = "A"
        readiness = "Strong"
    elif final_score >= 60:
        grade = "B"
        readiness = "Good"
    elif final_score >= 45:
        grade = "C"
        readiness = "Average"
    else:
        grade = "D"
        readiness = "Needs Improvement"

    # Hashtags count
    hashtags = re.findall(r"#\w+", content)
    rec_tags = plat_info.get("hashtag_recommended", 2)
    if len(hashtags) > 5:
        hook_tips.append(f"Too many hashtags ({len(hashtags)}). Recommended for {plat} is ~{rec_tags}.")

    return {
        "score": final_score,
        "grade": grade,
        "viral_readiness": readiness,
        "platform": plat,
        "metrics": {
            "char_count": char_count,
            "char_limit": limit,
            "is_within_limit": char_count <= limit,
            "word_count": word_count,
            "sentence_count": sentence_count,
            "line_count": line_count,
            "reading_time_sec": round((word_count / 200) * 60, 1),
            "flesch_reading_ease": round(flesch_score, 1),
            "reading_grade_level": round(fk_grade, 1),
            "power_words_count": len(found_power),
            "emoji_count": emoji_count,
            "hashtag_count": len(hashtags),
            "has_cta": has_cta,
        },
        "breakdown": {
            "hook_strength": hook_score,
            "formatting": formatting_score,
            "cta_engagement": cta_score,
            "readability": round((flesch_score / 100) * 20, 1),
        },
        "recommendations": hook_tips if hook_tips else ["Great structure, strong hook, and clean formatting! Ready to publish."],
    }


def get_diagnostics_engine(platform_query: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve system diagnostics, platform specs, and engine status."""
    limits = PLATFORM_LIMITS
    if platform_query and platform_query.lower() in limits:
        selected_limits = {platform_query.lower(): limits[platform_query.lower()]}
    else:
        selected_limits = limits

    return {
        "engine": "Omnipost Social Engine",
        "version": "1.0.0",
        "python_version": sys_platform.python_version(),
        "os": sys_platform.system(),
        "os_release": sys_platform.release(),
        "architecture": sys_platform.machine(),
        "unicode_support": sys.stdout.encoding or "utf-8",
        "platform_limits": selected_limits,
        "available_unicode_styles": list(UNICODE_MAPS.keys()) + ["underline", "strikethrough"],
        "available_export_formats": ["json", "csv", "markdown", "txt"],
    }


# Client Config Generator
def get_client_configs(
    server_cmd: Optional[str] = None,
    python_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate drop-in Model Context Protocol (MCP) server configuration snippets
    for Claude Desktop, Cursor, Cline, and Zed.
    """
    py = python_path or sys.executable
    args = ["-m", "omnipost_social_engine.cli", "mcp"] if not server_cmd else [server_cmd]

    claude_desktop = {
        "mcpServers": {
            "omnipost": {
                "command": py,
                "args": args,
                "env": {
                    "PYTHONIOENCODING": "utf-8",
                },
            }
        }
    }

    cursor_mcp = {
        "mcpServers": {
            "omnipost": {
                "command": py,
                "args": args,
            }
        }
    }

    cline_mcp = {
        "mcpServers": {
            "omnipost": {
                "command": py,
                "args": args,
                "disabled": False,
                "alwaysAllow": [
                    "omni_format_post",
                    "omni_split_thread",
                    "omni_generate_hooks",
                    "omni_analyze_engagement",
                    "omni_export_campaign",
                    "omni_get_diagnostics",
                    "omni_audit_accessibility",
                ],
            }
        }
    }

    zed_config = {
        "context_servers": {
            "omnipost": {
                "command": py,
                "args": args,
            }
        }
    }

    return {
        "claude_desktop": claude_desktop,
        "cursor": cursor_mcp,
        "cline": cline_mcp,
        "zed": zed_config,
    }


class MCPServer:
    """
    Stdio Model Context Protocol (MCP) JSON-RPC 2.0 Server.
    Provides tools to AI agents across Claude Desktop, Cursor, Cline, and Zed.
    """

    PROTOCOL_VERSION = "2024-11-05"
    SERVER_NAME = "omnipost-mcp-server"
    SERVER_VERSION = "1.0.0"

    def __init__(self, stdin_stream: Optional[Any] = None, stdout_stream: Optional[Any] = None):
        self.stdin = stdin_stream or sys.stdin
        self.stdout = stdout_stream or sys.stdout
        self.tools: Dict[str, Dict[str, Any]] = self._register_tools()

    def _register_tools(self) -> Dict[str, Dict[str, Any]]:
        """Declare tool specifications matching MCP specification."""
        return {
            "omni_format_post": {
                "description": "Format, optimize and style social media posts for target platform (twitter, linkedin, bluesky, threads, mastodon) with character checks and Unicode typography styles.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The raw post text content to format.",
                        },
                        "platform": {
                            "type": "string",
                            "description": "Target social media platform (twitter, linkedin, bluesky, threads, mastodon).",
                            "enum": ["twitter", "linkedin", "bluesky", "threads", "mastodon", "facebook", "instagram"],
                            "default": "twitter",
                        },
                        "style": {
                            "type": "string",
                            "description": "Unicode typography style (normal, bold, italic, bold_italic, monospace, script, double_struck, sans, underline, strikethrough).",
                            "default": "normal",
                        },
                        "hashtags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional list of hashtags to append.",
                        },
                        "trim": {
                            "type": "boolean",
                            "description": "Whether to strip leading/trailing whitespace.",
                            "default": True,
                        },
                    },
                    "required": ["text"],
                },
                "handler": self._handle_format_post,
            },
            "omni_split_thread": {
                "description": "Split long-form copy into platform-optimized thread posts with character limit adherence, natural sentence/paragraph breaks, and numbering markers.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Long text content to split into thread segments.",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum character limit per post (defaults to platform limit).",
                            "default": 280,
                        },
                        "platform": {
                            "type": "string",
                            "description": "Target platform for character limit autodetection.",
                            "default": "twitter",
                        },
                        "numbering": {
                            "type": "boolean",
                            "description": "Whether to append/prepend thread numbering (e.g. 1/N).",
                            "default": True,
                        },
                        "numbering_format": {
                            "type": "string",
                            "description": "Numbering format: 'fraction' (1/N), 'fraction_thread' (🧵 1/N), 'bracket' ([1/N]), 'counter' (1.).",
                            "enum": ["fraction", "fraction_thread", "bracket", "counter"],
                            "default": "fraction",
                        },
                    },
                    "required": ["text"],
                },
                "handler": self._handle_split_thread,
            },
            "omni_generate_hooks": {
                "description": "Generate high-converting viral hooks, headlines, and opening lines based on proven copywriting frameworks.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "The topic, product, or central theme.",
                        },
                        "niche": {
                            "type": "string",
                            "description": "Target audience niche (e.g. tech, saas, creator, ai, finance).",
                            "default": "tech",
                        },
                        "framework": {
                            "type": "string",
                            "description": "Copywriting framework: contrarian, question, number_list, curiosity_gap, transformation, how_to, negative_bias, secret_mistake, story_lead, or all.",
                            "default": "all",
                        },
                        "count": {
                            "type": "integer",
                            "description": "Number of hook variations to generate.",
                            "default": 10,
                        },
                    },
                    "required": ["topic"],
                },
                "handler": self._handle_generate_hooks,
            },
            "omni_analyze_engagement": {
                "description": "Analyze text for engagement potential, viral readiness score (0-100), readability metrics, sentiment, structure, and actionable optimization tips.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Post text to analyze.",
                        },
                        "platform": {
                            "type": "string",
                            "description": "Target platform for contextual scoring.",
                            "default": "twitter",
                        },
                    },
                    "required": ["text"],
                },
                "handler": self._handle_analyze_engagement,
            },
            "omni_export_campaign": {
                "description": "Export a multi-post social campaign into Buffer/Hootsuite CSV, JSON bundle, Markdown calendar, or plain text.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "campaign": {
                            "type": ["object", "array", "string"],
                            "description": "Campaign dictionary, list of posts, or raw text.",
                        },
                        "format": {
                            "type": "string",
                            "description": "Export format: 'json', 'csv', 'markdown' / 'md', 'txt' / 'raw'.",
                            "enum": ["json", "csv", "markdown", "md", "txt", "raw"],
                            "default": "json",
                        },
                        "preset": {
                            "type": "string",
                            "description": "CSV preset: 'buffer', 'hootsuite', 'typefully', 'generic'.",
                            "default": "buffer",
                        },
                    },
                    "required": ["campaign"],
                },
                "handler": self._handle_export_campaign,
            },
            "omni_get_diagnostics": {
                "description": "Retrieve system diagnostics, platform character limits, Unicode font support status, and engine version info.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "platform": {
                            "type": "string",
                            "description": "Optional specific platform query.",
                        },
                    },
                },
                "handler": self._handle_get_diagnostics,
            },
            "omni_audit_accessibility": {
                "description": "Audit alt-text against WCAG 2.2 accessibility standards and detect content warning (CW) triggers for sensitive posts.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "alt_text": {
                            "type": "string",
                            "description": "Image alt-text description to audit.",
                            "default": "",
                        },
                        "post_text": {
                            "type": "string",
                            "description": "Accompanying post body to scan for content warnings (CW).",
                            "default": "",
                        },
                        "platform": {
                            "type": "string",
                            "description": "Target social platform (twitter, bluesky, mastodon, threads, linkedin).",
                            "default": "twitter",
                        },
                    },
                },
                "handler": self._handle_audit_accessibility,
            },
        }

    # Tool Handlers
    def _handle_format_post(self, args: Dict[str, Any]) -> str:
        text = args.get("text", "")
        platform = args.get("platform", "twitter")
        style = args.get("style", "normal")
        hashtags = args.get("hashtags")
        trim = args.get("trim", True)
        res = format_post_engine(text=text, platform=platform, style=style, hashtags=hashtags, trim=trim)
        return json.dumps(res, indent=2, ensure_ascii=False)

    def _handle_split_thread(self, args: Dict[str, Any]) -> str:
        text = args.get("text", "")
        limit = args.get("limit", 280)
        platform = args.get("platform", "twitter")
        numbering = args.get("numbering", True)
        numbering_format = args.get("numbering_format", "fraction")
        res = split_thread_engine(
            text=text,
            limit=limit,
            platform=platform,
            numbering=numbering,
            numbering_format=numbering_format,
        )
        return json.dumps(res, indent=2, ensure_ascii=False)

    def _handle_generate_hooks(self, args: Dict[str, Any]) -> str:
        topic = args.get("topic", "")
        niche = args.get("niche", "tech")
        framework = args.get("framework", "all")
        count = args.get("count", 10)
        res = generate_hooks_engine(topic=topic, niche=niche, framework=framework, count=count)
        return json.dumps(res, indent=2, ensure_ascii=False)

    def _handle_analyze_engagement(self, args: Dict[str, Any]) -> str:
        text = args.get("text", "")
        platform = args.get("platform", "twitter")
        res = analyze_engagement_engine(text=text, platform=platform)
        return json.dumps(res, indent=2, ensure_ascii=False)

    def _handle_export_campaign(self, args: Dict[str, Any]) -> str:
        campaign_data = args.get("campaign", {})
        fmt = args.get("format", "json")
        preset = args.get("preset", "buffer")
        exported = CampaignExporter.export(campaign_data, format=fmt, preset=preset)
        return exported

    def _handle_get_diagnostics(self, args: Dict[str, Any]) -> str:
        plat = args.get("platform")
        res = get_diagnostics_engine(plat)
        return json.dumps(res, indent=2, ensure_ascii=False)

    def _handle_audit_accessibility(self, args: Dict[str, Any]) -> str:
        alt_text = args.get("alt_text", "")
        post_text = args.get("post_text", "")
        platform = args.get("platform", "twitter")
        res = evaluate_accessibility_suite(alt_text=alt_text, post_text=post_text, platform=platform)
        return json.dumps(res, indent=2, ensure_ascii=False)

    # JSON-RPC Message Processing
    def process_message(self, message_str: str) -> Optional[str]:
        """Process a single JSON-RPC 2.0 message string and return serialized response."""
        if not message_str or not message_str.strip():
            return None

        try:
            req = json.loads(message_str)
        except json.JSONDecodeError as e:
            return json.dumps({
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {str(e)}"},
            })

        req_id = req.get("id")
        method = req.get("method")
        params = req.get("params", {})

        # Handle Notifications (no response expected)
        if method == "notifications/initialized":
            return None

        # Handle Standard Methods
        if method == "initialize":
            res = {
                "protocolVersion": self.PROTOCOL_VERSION,
                "capabilities": {
                    "tools": {
                        "listChanged": False,
                    }
                },
                "serverInfo": {
                    "name": self.SERVER_NAME,
                    "version": self.SERVER_VERSION,
                },
            }
            return json.dumps({"jsonrpc": "2.0", "id": req_id, "result": res})

        elif method == "ping":
            return json.dumps({"jsonrpc": "2.0", "id": req_id, "result": {}})

        elif method == "tools/list":
            tools_list = []
            for name, defn in self.tools.items():
                tools_list.append({
                    "name": name,
                    "description": defn["description"],
                    "inputSchema": defn["inputSchema"],
                })
            return json.dumps({"jsonrpc": "2.0", "id": req_id, "result": {"tools": tools_list}})

        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})

            if tool_name not in self.tools:
                return json.dumps({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Tool '{tool_name}' not found"},
                })

            handler = self.tools[tool_name]["handler"]
            try:
                output_str = handler(tool_args)
                result = {
                    "content": [
                        {
                            "type": "text",
                            "text": output_str,
                        }
                    ],
                    "isError": False,
                }
                return json.dumps({"jsonrpc": "2.0", "id": req_id, "result": result})
            except Exception as ex:
                result = {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Error executing tool '{tool_name}': {str(ex)}",
                        }
                    ],
                    "isError": True,
                }
                return json.dumps({"jsonrpc": "2.0", "id": req_id, "result": result})

        else:
            if req_id is not None:
                return json.dumps({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Method '{method}' not found"},
                })
            return None

    def run_stdio(self) -> None:
        """Run stdio JSON-RPC loop until EOF."""
        try:
            for line in self.stdin:
                line = line.strip()
                if not line:
                    continue
                response = self.process_message(line)
                if response:
                    self.stdout.write(response + "\n")
                    self.stdout.flush()
        except (KeyboardInterrupt, BrokenPipeError):
            pass


def run_mcp_server() -> None:
    """Entry point for running stdio MCP server."""
    server = MCPServer()
    server.run_stdio()
