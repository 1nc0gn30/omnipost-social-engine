"""
Omnipost Social Engine - Campaign Exporter
Multi-format campaign exporter supporting JSON bundles, CSV calendars (Buffer, Hootsuite, Typefully),
Markdown schedules, and raw text output with zero external dependencies.
"""

from __future__ import annotations

import csv
import datetime
import io
import json
import os
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Union


# Standard Platform Character & Media Limits
PLATFORM_LIMITS: Dict[str, Dict[str, Any]] = {
    "twitter": {
        "name": "Twitter / X",
        "char_limit": 280,
        "media_limit": 4,
        "thread_supported": True,
        "hashtag_recommended": 2,
    },
    "bluesky": {
        "name": "Bluesky",
        "char_limit": 300,
        "media_limit": 4,
        "thread_supported": True,
        "hashtag_recommended": 3,
    },
    "threads": {
        "name": "Meta Threads",
        "char_limit": 500,
        "media_limit": 10,
        "thread_supported": True,
        "hashtag_recommended": 1,
    },
    "mastodon": {
        "name": "Mastodon",
        "char_limit": 500,
        "media_limit": 4,
        "thread_supported": True,
        "hashtag_recommended": 5,
    },
    "linkedin": {
        "name": "LinkedIn",
        "char_limit": 3000,
        "media_limit": 9,
        "thread_supported": False,
        "hashtag_recommended": 4,
    },
    "facebook": {
        "name": "Facebook",
        "char_limit": 2200,
        "media_limit": 10,
        "thread_supported": False,
        "hashtag_recommended": 2,
    },
    "instagram": {
        "name": "Instagram",
        "char_limit": 2200,
        "media_limit": 10,
        "thread_supported": False,
        "hashtag_recommended": 8,
    },
}


@dataclass
class Post:
    """Represents an individual social media post within a campaign."""
    content: str
    id: Optional[str] = None
    title: Optional[str] = None
    platform: str = "twitter"
    scheduled_time: Optional[str] = None
    hashtags: List[str] = field(default_factory=list)
    media_urls: List[str] = field(default_factory=list)
    thread_position: Optional[int] = None
    total_thread_posts: Optional[int] = None
    status: str = "draft"  # draft, scheduled, published, archived
    notes: Optional[str] = None
    extra_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert post to dictionary representation."""
        data = asdict(self)
        # Clean up None values if desired
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Post:
        """Create a Post instance from a dictionary."""
        content = data.get("content") or data.get("text") or ""
        hashtags = data.get("hashtags", [])
        if isinstance(hashtags, str):
            hashtags = [h.strip() for h in hashtags.replace(",", " ").split() if h.strip()]
        
        media_urls = data.get("media_urls") or data.get("media") or []
        if isinstance(media_urls, str):
            media_urls = [m.strip() for m in media_urls.split(",") if m.strip()]

        return cls(
            id=str(data.get("id") or ""),
            title=data.get("title"),
            content=content,
            platform=data.get("platform", "twitter").lower(),
            scheduled_time=data.get("scheduled_time") or data.get("date") or data.get("time"),
            hashtags=hashtags,
            media_urls=media_urls,
            thread_position=data.get("thread_position"),
            total_thread_posts=data.get("total_thread_posts"),
            status=data.get("status", "draft"),
            notes=data.get("notes"),
            extra_metadata=data.get("extra_metadata", {}),
        )


@dataclass
class Campaign:
    """Represents a scheduled campaign containing multiple social posts."""
    name: str = "Untitled Campaign"
    description: Optional[str] = None
    posts: List[Post] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    version: str = "1.0.0"
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_post(self, post: Union[Post, Dict[str, Any]]) -> Post:
        """Add a post to the campaign."""
        if isinstance(post, dict):
            p = Post.from_dict(post)
        else:
            p = post
        if not p.id:
            p.id = f"post_{len(self.posts) + 1}"
        self.posts.append(p)
        return p

    def to_dict(self) -> Dict[str, Any]:
        """Convert campaign to serializable dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at,
            "version": self.version,
            "tags": self.tags,
            "metadata": self.metadata,
            "total_posts": len(self.posts),
            "posts": [p.to_dict() for p in self.posts],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Campaign:
        """Construct Campaign instance from dictionary."""
        name = data.get("name", "Untitled Campaign")
        description = data.get("description")
        created_at = data.get("created_at") or datetime.datetime.now(datetime.timezone.utc).isoformat()
        version = data.get("version", "1.0.0")
        tags = data.get("tags", [])
        metadata = data.get("metadata", {})

        posts_data = data.get("posts", [])
        posts = [Post.from_dict(p) if isinstance(p, dict) else p for p in posts_data]

        return cls(
            name=name,
            description=description,
            posts=posts,
            created_at=created_at,
            version=version,
            tags=tags,
            metadata=metadata,
        )


class CampaignExporter:
    """
    Exports social media campaigns into multiple distribution formats:
    - JSON Bundle (Full schema with metadata)
    - CSV Schedules (Buffer, Hootsuite, Typefully, Generic)
    - Markdown Schedules (Calendar tables, rich cards, checklists)
    - Plain Text (Raw queue view)
    """

    @staticmethod
    def parse_campaign(data: Union[Campaign, Dict[str, Any], List[Dict[str, Any]], str]) -> Campaign:
        """
        Normalize input into a Campaign instance.
        Accepts Campaign instance, dictionary, list of posts, JSON string, or file path.
        """
        if isinstance(data, Campaign):
            return data

        if isinstance(data, list):
            camp = Campaign()
            for idx, item in enumerate(data, 1):
                if isinstance(item, dict):
                    if "id" not in item:
                        item["id"] = f"post_{idx}"
                    camp.add_post(item)
                elif isinstance(item, Post):
                    camp.add_post(item)
            return camp

        if isinstance(data, dict):
            return Campaign.from_dict(data)

        if isinstance(data, str):
            # Check if it's a file path
            if os.path.isfile(data):
                with open(data, "r", encoding="utf-8") as f:
                    content = f.read()
                try:
                    loaded = json.loads(content)
                    return CampaignExporter.parse_campaign(loaded)
                except json.JSONDecodeError:
                    # Treat lines as separate posts
                    camp = Campaign(name=os.path.basename(data))
                    for line in content.splitlines():
                        line = line.strip()
                        if line:
                            camp.add_post({"content": line})
                    return camp

            # Try parsing as JSON string
            try:
                loaded = json.loads(data)
                return CampaignExporter.parse_campaign(loaded)
            except json.JSONDecodeError:
                # Treat raw string as a single post campaign
                camp = Campaign()
                camp.add_post({"content": data})
                return camp

        raise ValueError(f"Unsupported campaign input type: {type(data)}")

    @classmethod
    def to_json(cls, campaign: Union[Campaign, Dict[str, Any], List[Dict[str, Any]], str], indent: int = 2) -> str:
        """Export campaign to formatted JSON bundle string."""
        camp = cls.parse_campaign(campaign)
        return json.dumps(camp.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def to_csv(
        cls,
        campaign: Union[Campaign, Dict[str, Any], List[Dict[str, Any]], str],
        preset: str = "buffer",
    ) -> str:
        """
        Export campaign to CSV format matching scheduling platforms.
        Presets:
        - 'buffer': Buffer CSV format (Date, Text, Media, Campaign)
        - 'hootsuite': Hootsuite bulk scheduler format (Date (MM/DD/YYYY hh:mm), Post, Link)
        - 'typefully': Typefully bulk import format (Scheduled Date, Content, Platform, Thread Position)
        - 'generic': Comprehensive internal schema with all fields
        """
        camp = cls.parse_campaign(campaign)
        output = io.StringIO()
        preset = preset.lower()

        if preset == "buffer":
            writer = csv.writer(output)
            writer.writerow(["Date", "Text", "Media", "Campaign"])
            for post in camp.posts:
                date_str = post.scheduled_time or ""
                # Format text with hashtags appended if not already present
                content = post.content
                if post.hashtags:
                    tags = " ".join(f"#{h.lstrip('#')}" for h in post.hashtags if f"#{h.lstrip('#')}" not in content)
                    if tags:
                        content = f"{content}\n\n{tags}"
                media_str = ", ".join(post.media_urls)
                writer.writerow([date_str, content, media_str, camp.name])

        elif preset == "hootsuite":
            writer = csv.writer(output)
            # Hootsuite standard: Date (MM/DD/YYYY hh:mm), Post, Link
            writer.writerow(["Date (MM/DD/YYYY hh:mm)", "Post", "Link"])
            for post in camp.posts:
                date_formatted = cls._format_hootsuite_date(post.scheduled_time)
                link = post.media_urls[0] if post.media_urls else ""
                writer.writerow([date_formatted, post.content, link])

        elif preset == "typefully":
            writer = csv.writer(output)
            writer.writerow(["Scheduled Date", "Content", "Platform", "Thread Position", "Notes"])
            for post in camp.posts:
                writer.writerow([
                    post.scheduled_time or "",
                    post.content,
                    post.platform,
                    post.thread_position or 1,
                    post.notes or "",
                ])

        else:  # 'generic'
            writer = csv.writer(output)
            writer.writerow([
                "ID",
                "Title",
                "Platform",
                "ScheduledTime",
                "Content",
                "Hashtags",
                "MediaURLs",
                "ThreadPosition",
                "Status",
                "Notes",
            ])
            for post in camp.posts:
                writer.writerow([
                    post.id or "",
                    post.title or "",
                    post.platform,
                    post.scheduled_time or "",
                    post.content,
                    ",".join(post.hashtags),
                    ",".join(post.media_urls),
                    post.thread_position or "",
                    post.status,
                    post.notes or "",
                ])

        return output.getvalue()

    @classmethod
    def to_markdown(
        cls,
        campaign: Union[Campaign, Dict[str, Any], List[Dict[str, Any]], str],
        view: str = "calendar",
    ) -> str:
        """
        Export campaign to formatted Markdown.
        Views:
        - 'calendar' / 'table': Clean Markdown table overview
        - 'cards': Detailed cards for each post with character stats & badges
        - 'checklist': Operational checklist with completion checkboxes
        """
        camp = cls.parse_campaign(campaign)
        lines: List[str] = []
        view = view.lower()

        lines.append(f"# 📅 Campaign Schedule: {camp.name}")
        if camp.description:
            lines.append(f"*{camp.description}*\n")
        else:
            lines.append("")

        lines.append(f"- **Total Posts**: {len(camp.posts)}")
        lines.append(f"- **Created At**: {camp.created_at}")
        if camp.tags:
            lines.append(f"- **Tags**: {', '.join(f'`{t}`' for t in camp.tags)}")
        lines.append("\n---\n")

        if view in ("cards", "card"):
            for idx, post in enumerate(camp.posts, 1):
                plat_info = PLATFORM_LIMITS.get(post.platform.lower(), {"name": post.platform, "char_limit": 280})
                char_count = len(post.content)
                limit = plat_info["char_limit"]
                valid = "✅ OK" if char_count <= limit else f"⚠️ Exceeds ({char_count}/{limit})"

                thread_badge = f" [Thread {post.thread_position}/{post.total_thread_posts}]" if post.thread_position else ""
                lines.append(f"### Post {idx}: {post.platform.title()}{thread_badge}")
                if post.scheduled_time:
                    lines.append(f"🕒 **Scheduled Time**: `{post.scheduled_time}` | **Status**: `{post.status}` | **Length**: {char_count}/{limit} ({valid})")
                else:
                    lines.append(f"🕒 **Scheduled Time**: `Unscheduled` | **Status**: `{post.status}` | **Length**: {char_count}/{limit} ({valid})")

                lines.append("\n```text")
                lines.append(post.content)
                lines.append("```\n")

                if post.hashtags:
                    tags_str = " ".join(f"#{h.lstrip('#')}" for h in post.hashtags)
                    lines.append(f"**Hashtags**: `{tags_str}`")

                if post.media_urls:
                    lines.append(f"**Media**: {', '.join(post.media_urls)}")

                if post.notes:
                    lines.append(f"💡 **Notes**: {post.notes}")

                lines.append("\n---\n")

        elif view in ("checklist", "check"):
            lines.append("## 📋 Execution Checklist\n")
            for idx, post in enumerate(camp.posts, 1):
                date_label = f"[{post.scheduled_time}] " if post.scheduled_time else ""
                thread_label = f" (🧵 {post.thread_position})" if post.thread_position else ""
                # Single line preview
                preview = post.content.replace("\n", " ")[:60] + ("..." if len(post.content) > 60 else "")
                lines.append(f"- [ ] **{date_label}{post.platform.upper()}{thread_label}**: {preview}")
            lines.append("")

        else:  # 'calendar' / 'table'
            lines.append("## 📊 Schedule Table\n")
            lines.append("| # | Scheduled Time | Platform | Status | Preview | Chars |")
            lines.append("|---|---|---|---|---|---|")
            for idx, post in enumerate(camp.posts, 1):
                time_str = post.scheduled_time or "TBD"
                preview = post.content.replace("\n", " ").replace("|", "\\|")[:50]
                if len(post.content) > 50:
                    preview += "..."
                limit = PLATFORM_LIMITS.get(post.platform.lower(), {}).get("char_limit", 280)
                char_str = f"{len(post.content)}/{limit}"
                lines.append(f"| {idx} | `{time_str}` | **{post.platform.title()}** | `{post.status}` | {preview} | {char_str} |")
            lines.append("")

        return "\n".join(lines)

    @classmethod
    def to_raw_text(
        cls,
        campaign: Union[Campaign, Dict[str, Any], List[Dict[str, Any]], str],
        delimiter: str = "\n\n" + "=" * 50 + "\n\n",
    ) -> str:
        """Export campaign as plain text blocks separated by delimiter."""
        camp = cls.parse_campaign(campaign)
        blocks: List[str] = []
        for idx, post in enumerate(camp.posts, 1):
            header_parts = [f"POST #{idx}", f"PLATFORM: {post.platform.upper()}"]
            if post.scheduled_time:
                header_parts.append(f"TIME: {post.scheduled_time}")
            if post.thread_position:
                header_parts.append(f"THREAD: {post.thread_position}")
            
            header = " | ".join(header_parts)
            body = post.content
            if post.hashtags:
                tags = " ".join(f"#{h.lstrip('#')}" for h in post.hashtags if f"#{h.lstrip('#')}" not in body)
                if tags:
                    body = f"{body}\n\n{tags}"
            blocks.append(f"{header}\n{'-' * len(header)}\n{body}")

        return delimiter.join(blocks)

    @classmethod
    def export(
        cls,
        campaign: Union[Campaign, Dict[str, Any], List[Dict[str, Any]], str],
        format: str = "json",
        preset: str = "buffer",
        view: str = "calendar",
        indent: int = 2,
    ) -> str:
        """
        Master export router.
        Format options: 'json', 'csv', 'md' / 'markdown', 'txt' / 'raw'.
        """
        fmt = format.lower().strip()
        if fmt == "json":
            return cls.to_json(campaign, indent=indent)
        elif fmt == "csv":
            return cls.to_csv(campaign, preset=preset)
        elif fmt in ("md", "markdown"):
            return cls.to_markdown(campaign, view=view)
        elif fmt in ("txt", "raw", "text"):
            return cls.to_raw_text(campaign)
        else:
            raise ValueError(f"Unsupported export format '{format}'. Choose from 'json', 'csv', 'markdown', 'txt'.")

    @classmethod
    def export_to_file(
        cls,
        campaign: Union[Campaign, Dict[str, Any], List[Dict[str, Any]], str],
        filepath: str,
        format: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """
        Export campaign directly to a local file, inferring format from extension if not specified.
        """
        if not format:
            ext = os.path.splitext(filepath)[1].lower().lstrip(".")
            format = "md" if ext == "markdown" else (ext if ext in ("json", "csv", "md", "txt") else "json")

        content = cls.export(campaign, format=format, **kwargs)
        parent_dir = os.path.dirname(filepath)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return filepath

    @staticmethod
    def _format_hootsuite_date(iso_str: Optional[str]) -> str:
        """Format an ISO date string into Hootsuite standard: MM/DD/YYYY hh:mm."""
        if not iso_str:
            return ""
        try:
            # Try parsing ISO
            dt = datetime.datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
            return dt.strftime("%m/%d/%Y %H:%M")
        except Exception:
            return iso_str

    @staticmethod
    def create_sample_campaign(name: str = "Omnipost Launch Campaign") -> Campaign:
        """Generate a realistic multi-platform campaign for demonstrations and testing."""
        camp = Campaign(
            name=name,
            description="Multi-platform product launch campaign for Omnipost Social Engine.",
            tags=["launch", "product", "growth", "ai"],
        )
        camp.add_post({
            "id": "post_1",
            "title": "Teaser Hook",
            "platform": "twitter",
            "scheduled_time": "2026-09-20T14:00:00Z",
            "content": "Most developers spend 4+ hours formatting copy for 5 different social networks.\n\nWe built a zero-dependency CLI engine that automates it in 200ms.\n\nHere is how it works 🧵👇",
            "hashtags": ["buildinpublic", "devtools", "python"],
            "thread_position": 1,
            "total_thread_posts": 3,
            "status": "scheduled",
        })
        camp.add_post({
            "id": "post_2",
            "title": "Architecture Deep Dive",
            "platform": "twitter",
            "scheduled_time": "2026-09-20T14:01:00Z",
            "content": "1/ Zero external dependencies.\n2/ Standalone stdio MCP server for Claude & Cursor.\n3/ Material 3 UI Studio served over local HTTP.\n4/ Automatic Unicode typography styling.\n\nEverything in pure Python 3.13 stdlib.",
            "hashtags": ["python", "opensource"],
            "thread_position": 2,
            "total_thread_posts": 3,
            "status": "scheduled",
        })
        camp.add_post({
            "id": "post_3",
            "title": "CTA & Link",
            "platform": "twitter",
            "scheduled_time": "2026-09-20T14:02:00Z",
            "content": "Try it now with `pip install omnipost-social-engine` or run `omnipost serve` to open the local Studio.\n\nStar the repo on GitHub: https://github.com/omnipost/social-engine",
            "hashtags": ["ai", "mcp"],
            "thread_position": 3,
            "total_thread_posts": 3,
            "status": "scheduled",
        })
        camp.add_post({
            "id": "post_4",
            "title": "LinkedIn Longform Story",
            "platform": "linkedin",
            "scheduled_time": "2026-09-21T13:30:00Z",
            "content": "Why we rejected a 300MB node_modules stack for our social automation engine:\n\nLast month, we audited our team's social publishing workflow. We were juggling 4 different SaaS tabs, fighting character count truncations, and fixing broken line breaks on mobile.\n\nInstead of subscribing to another $99/mo tool, we engineered Omnipost:\n- 100% offline & local-first\n- Native Model Context Protocol (MCP) server\n- Automatic platform compliance checks\n\nSimplicity scales.",
            "hashtags": ["Engineering", "Productivity", "OpenSource", "DeveloperTools"],
            "status": "scheduled",
            "notes": "Tag contributors in the comments after posting.",
        })
        return camp
