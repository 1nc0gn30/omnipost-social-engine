"""
Unit tests for Command Line Interface (CLI) in omnipost_social_engine.
"""

import json
import os
import tempfile
import pytest

from omnipost_social_engine.cli import main


class TestCLIExecution:
    def test_cli_no_args_shows_banner_and_exits_0(self, capsys):
        ret = main([])
        assert ret == 0
        captured = capsys.readouterr()
        assert "OMNIPOST SOCIAL ENGINE" in captured.out

    def test_cli_format_basic(self, capsys):
        ret = main(["format", "Test tweet content", "--platform", "twitter"])
        assert ret == 0
        captured = capsys.readouterr()
        assert "Twitter / X" in captured.out
        assert "Test tweet content" in captured.out

    def test_cli_format_styled_json(self, capsys):
        ret = main(["format", "Bold headline", "--style", "bold", "--json"])
        assert ret == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "𝗕𝗼𝗹𝗱" in data["text"]
        assert data["is_valid"] is True

    def test_cli_format_file_and_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            in_file = os.path.join(tmpdir, "in.txt")
            out_file = os.path.join(tmpdir, "out.txt")
            with open(in_file, "w", encoding="utf-8") as f:
                f.write("Post content from file")

            ret = main(["format", in_file, "--platform", "linkedin", "--out", out_file])
            assert ret == 0
            assert os.path.exists(out_file)
            with open(out_file, "r", encoding="utf-8") as f:
                assert f.read().strip() == "Post content from file"

    def test_cli_split_basic(self, capsys):
        text = "Paragraph one with detail.\n\nParagraph two with more details."
        ret = main(["split", text, "--limit", "40"])
        assert ret == 0
        captured = capsys.readouterr()
        assert "Thread Split Results" in captured.out
        assert "[Post 1/" in captured.out

    def test_cli_split_json(self, capsys):
        text = "Short text"
        ret = main(["split", text, "--json"])
        assert ret == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["total_posts"] == 1

    def test_cli_hooks_generation(self, capsys):
        ret = main(["hooks", "NextJS Performance", "--count", "5", "--niche", "frontend"])
        assert ret == 0
        captured = capsys.readouterr()
        assert "Viral Hooks for:" in captured.out
        assert "NextJS Performance" in captured.out

    def test_cli_hooks_json(self, capsys):
        ret = main(["hooks", "Indie Hacking", "--json"])
        assert ret == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert len(data["hooks"]) == 10

    def test_cli_analyze_post(self, capsys):
        text = "Why 90% of developers struggle with social media. Thread 👇\n\n1. Overthinking\n2. Inconsistency"
        ret = main(["analyze", text, "--platform", "twitter"])
        assert ret == 0
        captured = capsys.readouterr()
        assert "Social Engagement Score:" in captured.out
        assert "Metrics:" in captured.out

    def test_cli_analyze_json(self, capsys):
        text = "Simple post"
        ret = main(["analyze", text, "--json"])
        assert ret == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "score" in data
        assert "grade" in data

    def test_cli_export_to_csv(self, capsys):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            f.write(json.dumps({
                "name": "CLI Export Test",
                "posts": [{"content": "Exported post", "platform": "twitter"}],
            }))
            tmp_json = f.name

        try:
            ret = main(["export", tmp_json, "--format", "csv", "--preset", "buffer"])
            assert ret == 0
            captured = capsys.readouterr()
            assert "Date,Text,Media,Campaign" in captured.out
            assert "Exported post" in captured.out
        finally:
            if os.path.exists(tmp_json):
                os.remove(tmp_json)

    def test_cli_mcp_config(self, capsys):
        ret = main(["mcp-config", "--client", "all"])
        assert ret == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "claude_desktop" in data
        assert "cursor" in data

    def test_cli_platform_diagnostics(self, capsys):
        ret = main(["platform", "--json"])
        assert ret == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["engine"] == "Omnipost Social Engine"
        assert "twitter" in data["platform_limits"]

    def test_cli_accessibility_audit(self, capsys):
        ret = main(["accessibility", "--alt", "Image of our new UI dashboard with metrics.", "--post", "Check this out!"])
        assert ret == 0
        captured = capsys.readouterr()
        assert "Accessibility & Content Warning Audit" in captured.out
        assert "Alt-Text Quality Score" in captured.out

    def test_cli_accessibility_json(self, capsys):
        ret = main(["a11y", "--alt", "A sleek dark mode IDE screenshot.", "--post", "Spoiler: update is live!", "--json"])
        assert ret == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["alt_evaluation"]["is_valid_length"] is True
        assert data["content_warning"]["needs_cw"] is True
