"""Thread splitting engine for long-form articles, essays, and multi-card social posts.

Splits long texts into numbered social thread cards (Twitter/X, BlueSky, Threads, Mastodon)
with intelligent sentence boundary preservation, markdown code-block handling,
and custom hook/CTA integration.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from omnipost_social_engine.formatter import SocialFormatter


class NumberingStyle(str, Enum):
    """Supported numbering styles for social threads."""

    SLASH_TOTAL = "slash_total"  # 1/N, 2/N
    THREAD_EMOJI = "thread_emoji"  # 🧵 1/N, 🧵 2/N
    DOT_NUMBER = "dot_number"  # 1., 2.
    PARENTHESES = "parentheses"  # (1/N), (2/N)
    EMOJI_COUNTER = "emoji_counter"  # 1️⃣, 2️⃣
    CLEAN_SLASH = "clean_slash"  # 1/, 2/
    NONE = "none"


NUMBER_EMOJIS = {
    1: "1️⃣",
    2: "2️⃣",
    3: "3️⃣",
    4: "4️⃣",
    5: "5️⃣",
    6: "6️⃣",
    7: "7️⃣",
    8: "8️⃣",
    9: "9️⃣",
    10: "🔟",
}


@dataclass
class ThreadPost:
    """Represents a single post card within a thread."""

    index: int
    total: int
    content: str
    raw_content: str
    char_count: int
    is_hook: bool = False
    is_cta: bool = False
    has_code: bool = False
    has_quote: bool = False
    has_list: bool = False
    has_media_hint: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert post to serializable dictionary."""
        return {
            "index": self.index,
            "total": self.total,
            "content": self.content,
            "raw_content": self.raw_content,
            "char_count": self.char_count,
            "is_hook": self.is_hook,
            "is_cta": self.is_cta,
            "has_code": self.has_code,
            "has_quote": self.has_quote,
            "has_list": self.has_list,
            "has_media_hint": self.has_media_hint,
        }


class ThreadSplitter:
    """Intelligent multi-platform thread splitter."""

    DEFAULT_LIMITS = {
        "twitter": 280,
        "x": 280,
        "bluesky": 300,
        "bsky": 300,
        "threads": 500,
        "mastodon": 500,
        "linkedin": 3000,
    }

    def __init__(
        self,
        platform: str = "twitter",
        max_chars: Optional[int] = None,
        numbering_style: Union[str, NumberingStyle] = NumberingStyle.SLASH_TOTAL,
        numbering_position: str = "prefix",  # "prefix" or "suffix"
        use_twitter_weight: bool = True,
    ) -> None:
        """Initialize ThreadSplitter with platform limits and formatting preferences.

        Args:
            platform: Target platform ('twitter', 'bluesky', 'threads', 'mastodon', 'linkedin').
            max_chars: Optional custom character limit (overrides platform default).
            numbering_style: Thread numbering format (e.g. 'slash_total', 'thread_emoji').
            numbering_position: Where to place numbering tag: 'prefix' or 'suffix'.
            use_twitter_weight: If True and platform is Twitter/X, use Twitter weighted character counting.
        """
        self.platform = platform.lower()
        self.max_chars = max_chars or self.DEFAULT_LIMITS.get(self.platform, 280)
        if isinstance(numbering_style, str):
            try:
                self.numbering_style = NumberingStyle(numbering_style.lower())
            except ValueError:
                self.numbering_style = NumberingStyle.SLASH_TOTAL
        else:
            self.numbering_style = numbering_style
        self.numbering_position = numbering_position.lower()
        self.use_twitter_weight = use_twitter_weight and self.platform in ("twitter", "x")

    def _calculate_length(self, text: str) -> int:
        """Calculate length according to platform counting rules."""
        if self.use_twitter_weight:
            return SocialFormatter.calculate_twitter_length(text)
        return len(text)

    def _format_label(self, index: int, total: int) -> str:
        """Generate the thread numbering label for post at index out of total."""
        if self.numbering_style == NumberingStyle.NONE:
            return ""

        if self.numbering_style == NumberingStyle.SLASH_TOTAL:
            return f"{index}/{total}"
        elif self.numbering_style == NumberingStyle.THREAD_EMOJI:
            if index == 1:
                return f"🧵 1/{total}"
            return f"{index}/{total}"
        elif self.numbering_style == NumberingStyle.DOT_NUMBER:
            return f"{index}."
        elif self.numbering_style == NumberingStyle.PARENTHESES:
            return f"({index}/{total})"
        elif self.numbering_style == NumberingStyle.EMOJI_COUNTER:
            return NUMBER_EMOJIS.get(index, f"[{index}]")
        elif self.numbering_style == NumberingStyle.CLEAN_SLASH:
            return f"{index}/"
        return f"{index}/{total}"

    def _combine_label_and_content(self, label: str, raw_content: str) -> str:
        """Combine numbering label and raw content based on numbering position."""
        if not label:
            return raw_content.strip()

        clean_body = raw_content.strip()
        if not clean_body:
            return label

        if self.numbering_position == "suffix":
            return f"{clean_body}\n\n{label}"
        else:
            # Prefix
            return f"{label}\n\n{clean_body}"

    def _split_into_paragraphs(self, content: str) -> List[str]:
        """Split content into logical markdown blocks while protecting code blocks."""
        code_block_pattern = re.compile(r"```[\s\S]*?```", re.MULTILINE)
        code_blocks = list(code_block_pattern.finditer(content))

        if not code_blocks:
            # Regular markdown paragraphs
            blocks = [p.strip() for p in re.split(r"\n\s*\n", content) if p.strip()]
            return blocks

        # Segment with code blocks preserved
        blocks: List[str] = []
        last_end = 0

        for match in code_blocks:
            start, end = match.span()
            before_text = content[last_end:start].strip()
            if before_text:
                for p in re.split(r"\n\s*\n", before_text):
                    if p.strip():
                        blocks.append(p.strip())

            # Add the code block as a whole unit
            code_text = match.group(0).strip()
            blocks.append(code_text)
            last_end = end

        after_text = content[last_end:].strip()
        if after_text:
            for p in re.split(r"\n\s*\n", after_text):
                if p.strip():
                    blocks.append(p.strip())

        return blocks

    def _split_large_block(self, block: str, max_chunk_budget: int) -> List[str]:
        """Split a single oversized block into smaller pieces respecting sentences, clauses, or words."""
        # Check if block is a code block
        if block.startswith("```") and block.endswith("```"):
            return self._split_code_block(block, max_chunk_budget)

        # Try splitting by single line breaks / lists
        if "\n" in block:
            lines = [line.strip() for line in block.split("\n") if line.strip()]
            chunks: List[str] = []
            curr_lines: List[str] = []

            for line in lines:
                candidate = "\n".join(curr_lines + [line])
                if self._calculate_length(candidate) <= max_chunk_budget:
                    curr_lines.append(line)
                else:
                    if curr_lines:
                        chunks.append("\n".join(curr_lines))
                        curr_lines = []
                    if self._calculate_length(line) <= max_chunk_budget:
                        curr_lines.append(line)
                    else:
                        # Line itself is oversized
                        sub_chunks = self._split_by_sentences(line, max_chunk_budget)
                        chunks.extend(sub_chunks)

            if curr_lines:
                chunks.append("\n".join(curr_lines))
            return chunks

        return self._split_by_sentences(block, max_chunk_budget)

    def _split_code_block(self, code_block: str, max_chunk_budget: int) -> List[str]:
        """Split an oversized fenced code block while ensuring every chunk is enclosed with fences."""
        lines = code_block.split("\n")
        header = lines[0]  # e.g. ```python
        lang = header[3:].strip()
        footer = lines[-1] if lines[-1].startswith("```") else "```"
        body_lines = lines[1:-1] if lines[-1].startswith("```") else lines[1:]

        chunks: List[str] = []
        curr_lines: List[str] = []

        for line in body_lines:
            candidate_block = f"{header}\n" + "\n".join(curr_lines + [line]) + f"\n{footer}"
            if self._calculate_length(candidate_block) <= max_chunk_budget:
                curr_lines.append(line)
            else:
                if curr_lines:
                    chunks.append(f"{header}\n" + "\n".join(curr_lines) + f"\n{footer}")
                    curr_lines = []
                # If single line is too long, wrap it
                candidate_line_block = f"{header}\n{line}\n{footer}"
                if self._calculate_length(candidate_line_block) <= max_chunk_budget:
                    curr_lines.append(line)
                else:
                    # Split line directly
                    sub_words = line.split(" ")
                    sub_curr: List[str] = []
                    for w in sub_words:
                        test_str = " ".join(sub_curr + [w])
                        test_blk = f"{header}\n{test_str}\n{footer}"
                        if self._calculate_length(test_blk) <= max_chunk_budget:
                            sub_curr.append(w)
                        else:
                            if sub_curr:
                                chunks.append(f"{header}\n" + " ".join(sub_curr) + f"\n{footer}")
                                sub_curr = []
                            sub_curr.append(w)
                    if sub_curr:
                        curr_lines.append(" ".join(sub_curr))

        if curr_lines:
            chunks.append(f"{header}\n" + "\n".join(curr_lines) + f"\n{footer}")

        return chunks or [code_block]

    def _split_by_sentences(self, text: str, max_chunk_budget: int) -> List[str]:
        """Split text into sentences, clauses, or words to fit character budget."""
        # Split on sentence boundaries: (. ! ?) followed by whitespace
        sentence_endings = re.compile(r"(?<=[.!?])\s+")
        sentences = [s.strip() for s in sentence_endings.split(text) if s.strip()]

        chunks: List[str] = []
        current_chunk: List[str] = []

        for sentence in sentences:
            candidate = " ".join(current_chunk + [sentence]) if current_chunk else sentence
            if self._calculate_length(candidate) <= max_chunk_budget:
                current_chunk.append(sentence)
            else:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                    current_chunk = []

                if self._calculate_length(sentence) <= max_chunk_budget:
                    current_chunk.append(sentence)
                else:
                    # Split sentence by clauses (, ; : -)
                    clause_chunks = self._split_by_clauses(sentence, max_chunk_budget)
                    chunks.extend(clause_chunks)

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def _split_by_clauses(self, sentence: str, max_chunk_budget: int) -> List[str]:
        """Split sentence by comma, semicolon, dash, or colon."""
        clause_splits = re.split(r"([,;:\—–]|\s-\s)", sentence)
        reconstructed: List[str] = []
        temp = ""
        for part in clause_splits:
            if part in (",", ";", ":", "—", "–", " - "):
                temp += part
                reconstructed.append(temp.strip())
                temp = ""
            else:
                temp += part
        if temp.strip():
            reconstructed.append(temp.strip())

        chunks: List[str] = []
        current: List[str] = []

        for part in reconstructed:
            cand = " ".join(current + [part]) if current else part
            if self._calculate_length(cand) <= max_chunk_budget:
                current.append(part)
            else:
                if current:
                    chunks.append(" ".join(current))
                    current = []
                if self._calculate_length(part) <= max_chunk_budget:
                    current.append(part)
                else:
                    # Split by words
                    words = part.split()
                    w_curr: List[str] = []
                    for w in words:
                        w_cand = " ".join(w_curr + [w]) if w_curr else w
                        if self._calculate_length(w_cand) <= max_chunk_budget:
                            w_curr.append(w)
                        else:
                            if w_curr:
                                chunks.append(" ".join(w_curr))
                                w_curr = []
                            w_curr.append(w)
                    if w_curr:
                        current.append(" ".join(w_curr))

        if current:
            chunks.append(" ".join(current))

        return chunks

    def _chunk_blocks(self, blocks: List[str], max_body_budget: int) -> List[str]:
        """Group semantic blocks into raw post chunks that fit within max_body_budget."""
        chunks: List[str] = []
        current_blocks: List[str] = []

        for block in blocks:
            candidate = "\n\n".join(current_blocks + [block]) if current_blocks else block
            if self._calculate_length(candidate) <= max_body_budget:
                current_blocks.append(block)
            else:
                if current_blocks:
                    chunks.append("\n\n".join(current_blocks))
                    current_blocks = []

                if self._calculate_length(block) <= max_body_budget:
                    current_blocks.append(block)
                else:
                    # Oversized block: split internally
                    sub_blocks = self._split_large_block(block, max_body_budget)
                    for sub in sub_blocks:
                        if self._calculate_length(sub) <= max_body_budget:
                            chunks.append(sub)
                        else:
                            # Edge case: forced character chunk
                            chunks.append(sub[:max_body_budget])

        if current_blocks:
            chunks.append("\n\n".join(current_blocks))

        return chunks

    def split(
        self,
        content: str,
        hook: Optional[str] = None,
        cta: Optional[str] = None,
        max_chars: Optional[int] = None,
        preserve_code_blocks: bool = True,
    ) -> List[ThreadPost]:
        """Split content into a sequence of numbered ThreadPost objects.

        Args:
            content: The full article or markdown text to split.
            hook: Optional hook to ensure on the first card.
            cta: Optional call-to-action to append to the final card.
            max_chars: Override maximum character limit per card.
            preserve_code_blocks: Ensure markdown code fences are preserved.

        Returns:
            List of ThreadPost objects with indices, total count, and metadata.
        """
        limit = max_chars or self.max_chars
        clean_content = content.strip()

        # Build initial list of blocks
        blocks: List[str] = []
        if hook:
            blocks.append(hook.strip())

        raw_blocks = self._split_into_paragraphs(clean_content)
        # Avoid duplicating hook if it matches the first block
        if hook and raw_blocks and raw_blocks[0] == hook.strip():
            raw_blocks = raw_blocks[1:]

        blocks.extend(raw_blocks)

        if not blocks:
            return []

        # Two-pass calculation to ensure label + content <= limit
        # Start with an estimated label allowance (e.g. 10 chars for '🧵 99/99\n\n')
        label_allowance = 12 if self.numbering_style != NumberingStyle.NONE else 0

        # Iteratively refine chunks
        raw_chunks = self._chunk_blocks(blocks, limit - label_allowance)
        total_count = len(raw_chunks)

        # Handle CTA integration
        if cta:
            clean_cta = cta.strip()
            last_chunk = raw_chunks[-1] if raw_chunks else ""
            candidate_last = f"{last_chunk}\n\n{clean_cta}"
            sample_label = self._format_label(total_count, total_count)
            sample_post = self._combine_label_and_content(sample_label, candidate_last)

            if self._calculate_length(sample_post) <= limit:
                raw_chunks[-1] = candidate_last
            else:
                # Add CTA as dedicated final card
                raw_chunks.append(clean_cta)
                total_count = len(raw_chunks)

        # Verify and re-split if any card exceeds limit with exact label
        max_attempts = 4
        attempt = 0
        while attempt < max_attempts:
            needs_resplit = False
            total_count = len(raw_chunks)
            for idx, chunk in enumerate(raw_chunks, start=1):
                lbl = self._format_label(idx, total_count)
                full = self._combine_label_and_content(lbl, chunk)
                if self._calculate_length(full) > limit:
                    needs_resplit = True
                    label_allowance += 4
                    break

            if not needs_resplit:
                break

            # Re-chunk with increased allowance
            raw_chunks = self._chunk_blocks(blocks, limit - label_allowance)
            if cta and raw_chunks:
                clean_cta = cta.strip()
                last_chunk = raw_chunks[-1]
                cand = f"{last_chunk}\n\n{clean_cta}"
                lbl = self._format_label(len(raw_chunks), len(raw_chunks))
                if self._calculate_length(self._combine_label_and_content(lbl, cand)) <= limit:
                    raw_chunks[-1] = cand
                else:
                    raw_chunks.append(clean_cta)
            attempt += 1

        total_count = len(raw_chunks)
        posts: List[ThreadPost] = []

        for idx, chunk in enumerate(raw_chunks, start=1):
            label = self._format_label(idx, total_count)
            formatted_content = self._combine_label_and_content(label, chunk)
            length = self._calculate_length(formatted_content)

            is_first = idx == 1
            is_last = idx == total_count

            has_code = "```" in chunk
            has_quote = bool(re.search(r"(?:^|\n)\s*>\s*", chunk))
            has_list = bool(re.search(r"(?:^|\n)\s*(?:[-*•→]|\d+\.)\s+", chunk))
            has_media = bool(re.search(r"(\!\[.*?\]\(.*?\)|\[Image:.*?\]|<media>)", chunk))

            post = ThreadPost(
                index=idx,
                total=total_count,
                content=formatted_content,
                raw_content=chunk,
                char_count=length,
                is_hook=is_first and bool(hook or idx == 1),
                is_cta=is_last and bool(cta or idx == total_count),
                has_code=has_code,
                has_quote=has_quote,
                has_list=has_list,
                has_media_hint=has_media,
            )
            posts.append(post)

        return posts

    @classmethod
    def preview_thread(cls, posts: List[ThreadPost]) -> str:
        """Render a clean text preview of a thread with card dividers."""
        divider = "-" * 42
        output: List[str] = []
        for post in posts:
            output.append(f"Card {post.index}/{post.total} ({post.char_count} chars):")
            output.append(post.content)
            output.append(divider)
        return "\n".join(output)

    @classmethod
    def export_as_json(cls, posts: List[ThreadPost], indent: int = 2) -> str:
        """Export list of ThreadPost objects to a JSON string."""
        data = [p.to_dict() for p in posts]
        return json.dumps(data, indent=indent, ensure_ascii=False)

    @classmethod
    def merge_thread(cls, posts: List[ThreadPost]) -> str:
        """Reconstruct original article or combined text from thread posts."""
        return "\n\n".join(p.raw_content for p in posts)
