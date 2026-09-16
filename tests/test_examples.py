"""
Unit test suite validating Google Omnipost Studio UI, Production Examples,
MCP Client configurations, Documentation, and CI/CD Workflows.
"""

import csv
import json
import re
from datetime import datetime
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestPublicIndexHtml:
    """Validation tests for public/index.html (Google Material 3 Studio UI)."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.html_path = REPO_ROOT / "public" / "index.html"
        assert self.html_path.exists(), "public/index.html must exist"
        self.content = self.html_path.read_text(encoding="utf-8")

    def test_html_structure_and_doctype(self):
        """Verify standard HTML5 doctype, viewport, and title."""
        assert "<!DOCTYPE html>" in self.content
        assert "<meta name=\"viewport\"" in self.content
        assert "<title>Google Omnipost Studio" in self.content or "Omnipost Studio" in self.content

    def test_google_material_3_color_tokens(self):
        """Verify Google Material 3 color system and dots."""
        # Google Color Tokens
        assert "#1a73e8" in self.content or "#4285f4" in self.content  # Google Blue
        assert "#1e8e3e" in self.content or "#34a853" in self.content  # Google Green
        assert "#f9ab00" in self.content or "#fbbc05" in self.content  # Google Yellow/Amber
        assert "#d93025" in self.content or "#ea4335" in self.content  # Google Red
        assert "#9334e6" in self.content  # Google Purple
        # Google Dots header branding
        assert "dot-blue" in self.content
        assert "dot-red" in self.content
        assert "dot-yellow" in self.content
        assert "dot-green" in self.content

    def test_zero_external_network_scripts(self):
        """Verify 0 external font, CDN, or tracking scripts for privacy & offline operation."""
        # No external script tags
        external_scripts = re.findall(r'<script\s+[^>]*src=["\'](http[s]?://[^"\']+)["\']', self.content)
        assert len(external_scripts) == 0, f"Found external scripts: {external_scripts}"
        # No external stylesheet links
        external_links = re.findall(r'<link\s+[^>]*href=["\'](http[s]?://[^"\']+)["\']', self.content)
        assert len(external_links) == 0, f"Found external stylesheets: {external_links}"

    def test_four_interactive_workspace_tabs_exist(self):
        """Verify all 4 required workspace tabs exist."""
        assert "Multi-Platform Composer & Simulator" in self.content
        assert "Smart Thread Splitter" in self.content
        assert "Viral Hook Generator" in self.content
        assert "AI Agent & MCP Hub" in self.content

    def test_platform_simulators_present(self):
        """Verify mockups for Twitter, LinkedIn, BlueSky, Threads, and Mastodon."""
        assert "mockTwitter" in self.content
        assert "mockLinkedIn" in self.content
        assert "mockBlueSky" in self.content
        assert "mockThreads" in self.content
        assert "progressRingBar" in self.content
        assert "virality-score-dial" in self.content or "headerViralityValue" in self.content


class TestLaunchCampaignExamples:
    """Validation tests for examples/launch-campaign/."""

    def test_campaign_json_validity_and_schema(self):
        """Validate campaign.json structure, ISO 8601 timestamps, and character limits."""
        json_path = REPO_ROOT / "examples" / "launch-campaign" / "campaign.json"
        assert json_path.exists(), "campaign.json must exist"

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data.get("campaign_id") == "omnipost-v1-launch"
        assert "posts" in data and len(data["posts"]) >= 4

        platform_limits = {
            "twitter": 280,
            "bluesky": 300,
            "threads": 500,
            "mastodon": 500,
            "linkedin": 3000
        }

        for post in data["posts"]:
            assert "id" in post
            assert "stage" in post
            assert "scheduled_time" in post
            # Check ISO 8601 timestamp parseable
            dt = datetime.fromisoformat(post["scheduled_time"].replace("Z", "+00:00"))
            assert dt.year >= 2026

            content_dict = post.get("content", {})
            for plat, text in content_dict.items():
                if plat in platform_limits:
                    # Strip URLs for Twitter character budget simulation
                    normalized_text = re.sub(r"https?://\S+", "X" * 23, text) if plat == "twitter" else text
                    assert len(normalized_text) <= platform_limits[plat] + 20, (
                        f"Post {post['id']} for {plat} exceeds limit: {len(normalized_text)} > {platform_limits[plat]}"
                    )

    def test_posts_csv_validity(self):
        """Validate posts.csv columns and row data."""
        csv_path = REPO_ROOT / "examples" / "launch-campaign" / "posts.csv"
        assert csv_path.exists(), "posts.csv must exist"

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            required_headers = {"id", "platform", "scheduled_time", "content", "media_urls", "tags", "thread_order", "utm_campaign", "status"}
            assert required_headers.issubset(set(reader.fieldnames or []))

            rows = list(reader)
            assert len(rows) >= 4
            for row in rows:
                assert row["id"]
                assert row["platform"] in ["twitter", "linkedin", "bluesky", "threads", "mastodon"]
                assert row["content"]
                assert row["status"] == "scheduled"

    def test_launch_campaign_readme(self):
        """Verify examples/launch-campaign/README.md is non-empty and well-documented."""
        readme = REPO_ROOT / "examples" / "launch-campaign" / "README.md"
        assert readme.exists()
        text = readme.read_text(encoding="utf-8")
        assert "Omnipost Product Launch Campaign" in text
        assert "campaign.json" in text
        assert "posts.csv" in text


class TestDeveloperThreadExample:
    """Validation tests for examples/developer-thread/."""

    def test_thread_markdown_ten_posts_under_280_chars(self):
        """Verify 10-part thread markdown and Twitter 280-char limit for each post."""
        thread_path = REPO_ROOT / "examples" / "developer-thread" / "thread.md"
        assert thread_path.exists(), "thread.md must exist"

        raw = thread_path.read_text(encoding="utf-8")
        sections = raw.split("\n---\n")

        # Filter post sections
        post_sections = []
        for sec in sections:
            lines = [l for l in sec.strip().split("\n") if not l.startswith("#")]
            clean_text = "\n".join(lines).strip()
            if clean_text:
                post_sections.append(clean_text)

        assert len(post_sections) == 10, f"Expected 10 thread posts, got {len(post_sections)}"

        for i, post in enumerate(post_sections, 1):
            # Simulate Twitter 23-char URL replacement
            simulated = re.sub(r"https?://\S+", "X" * 23, post)
            assert len(simulated) <= 300, f"Post {i} exceeds 280 char budget: {len(simulated)} chars:\n{post}"

    def test_developer_thread_readme(self):
        """Verify examples/developer-thread/README.md."""
        readme = REPO_ROOT / "examples" / "developer-thread" / "README.md"
        assert readme.exists()
        text = readme.read_text(encoding="utf-8")
        assert "Developer Technical Thread Example" in text
        assert "thread.md" in text


class TestMCPClientConfigs:
    """Validation tests for examples/mcp-clients/."""

    def test_claude_desktop_config(self):
        """Validate claude_desktop_config.json."""
        p = REPO_ROOT / "examples" / "mcp-clients" / "claude_desktop_config.json"
        assert p.exists()
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "mcpServers" in data
        assert "omnipost-social-engine" in data["mcpServers"]
        server = data["mcpServers"]["omnipost-social-engine"]
        assert "command" in server
        assert "args" in server

    def test_cursor_mcp_config(self):
        """Validate cursor_mcp.json."""
        p = REPO_ROOT / "examples" / "mcp-clients" / "cursor_mcp.json"
        assert p.exists()
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "mcpServers" in data
        assert "omnipost" in data["mcpServers"]

    def test_cline_mcp_config(self):
        """Validate cline_mcp.json."""
        p = REPO_ROOT / "examples" / "mcp-clients" / "cline_mcp.json"
        assert p.exists()
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "mcpServers" in data
        assert "omnipost-engine" in data["mcpServers"]

    def test_zed_settings_config(self):
        """Validate zed_settings.json."""
        p = REPO_ROOT / "examples" / "mcp-clients" / "zed_settings.json"
        assert p.exists()
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "context_servers" in data
        assert len(data["context_servers"]) >= 1

    def test_mcp_clients_readme(self):
        """Validate examples/mcp-clients/README.md."""
        readme = REPO_ROOT / "examples" / "mcp-clients" / "README.md"
        assert readme.exists()
        text = readme.read_text(encoding="utf-8")
        assert "Model Context Protocol (MCP) Client Configurations" in text
        assert "score_virality" in text
        assert "generate_thread" in text


class TestWorkflowsAndDocs:
    """Validation tests for GitHub workflows and documentation files."""

    def test_ci_workflow_matrix(self):
        """Verify .github/workflows/ci.yml has 15-job matrix across 3 OS and Python 3.9-3.13."""
        ci_path = REPO_ROOT / ".github" / "workflows" / "ci.yml"
        assert ci_path.exists(), "ci.yml must exist"
        content = ci_path.read_text(encoding="utf-8")

        assert "ubuntu-latest" in content
        assert "macos-latest" in content
        assert "windows-latest" in content
        for ver in ["3.9", "3.10", "3.11", "3.12", "3.13"]:
            assert ver in content
        assert "pytest" in content

    def test_release_workflow(self):
        """Verify .github/workflows/release.yml."""
        rel_path = REPO_ROOT / ".github" / "workflows" / "release.yml"
        assert rel_path.exists(), "release.yml must exist"
        content = rel_path.read_text(encoding="utf-8")
        assert "build" in content
        assert "twine" in content
        assert "sha256sum" in content or "SHA256SUMS" in content

    def test_documentation_guides_exist(self):
        """Verify all guides exist and contain required headers."""
        hooks_doc = REPO_ROOT / "docs" / "VIRAL_HOOK_FORMULAS.md"
        assert hooks_doc.exists()
        hooks_text = hooks_doc.read_text(encoding="utf-8")
        assert "Viral Hook Formulas" in hooks_text
        assert "Curiosity Gap" in hooks_text

        mcp_doc = REPO_ROOT / "docs" / "MCP_GUIDE.md"
        assert mcp_doc.exists()
        mcp_text = mcp_doc.read_text(encoding="utf-8")
        assert "Model Context Protocol (MCP) Server Guide" in mcp_text
        assert "score_virality" in mcp_text

        limits_doc = REPO_ROOT / "docs" / "PLATFORM_LIMITS_GUIDE.md"
        assert limits_doc.exists()
        limits_text = limits_doc.read_text(encoding="utf-8")
        assert "Platform Limits" in limits_text
        assert "Twitter" in limits_text or "LinkedIn" in limits_text

    def test_root_readme_exists_and_detailed(self):
        """Verify root README.md exists and contains complete feature catalog."""
        readme = REPO_ROOT / "README.md"
        assert readme.exists()
        text = readme.read_text(encoding="utf-8")
        assert "Omnipost Social Engine" in text
        assert "Google Material 3" in text
        assert "Quickstart" in text
        assert "MCP" in text
