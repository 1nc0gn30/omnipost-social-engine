"""
Unit tests for Model Context Protocol (MCP) Server and core engines in omnipost_social_engine.
"""

import io
import json
import pytest

from omnipost_social_engine.mcp_server import (
    MCPServer,
    apply_unicode_style,
    format_post_engine,
    generate_hooks_engine,
    get_client_configs,
    get_diagnostics_engine,
    split_thread_engine,
    analyze_engagement_engine,
    UNICODE_MAPS,
)


class TestUnicodeStylesAndFormatting:
    def test_unicode_bold_conversion(self):
        styled = apply_unicode_style("Hello World 123", "bold")
        assert "𝗛𝗲𝗹𝗹𝗼" in styled
        assert "𝟭𝟮𝟯" in styled

    def test_unicode_italic_conversion(self):
        styled = apply_unicode_style("Fast Python", "italic")
        assert "𝘍𝘢𝘴𝘵" in styled

    def test_unicode_monospace_conversion(self):
        styled = apply_unicode_style("Code 42", "monospace")
        assert "𝙲𝚘𝚍𝚎" in styled
        assert "𝟺𝟸" in styled

    def test_unicode_underline_and_strikethrough(self):
        u = apply_unicode_style("Test", "underline")
        assert "\u0332" in u
        s = apply_unicode_style("Test", "strikethrough")
        assert "\u0336" in s

    def test_format_post_engine_valid_and_limits(self):
        res = format_post_engine("Short tweet", platform="twitter", style="normal")
        assert res["is_valid"] is True
        assert res["char_count"] == 11
        assert res["char_limit"] == 280
        assert res["remaining_chars"] == 269

    def test_format_post_engine_with_hashtags(self):
        res = format_post_engine("Check this out", platform="bluesky", hashtags=["python", "#ai"])
        assert "#python" in res["text"]
        assert "#ai" in res["text"]
        assert res["char_limit"] == 300


class TestThreadSplitterEngine:
    def test_split_short_text(self):
        text = "This is a single short sentence."
        res = split_thread_engine(text, limit=280)
        assert res["total_posts"] == 1
        assert res["posts"][0]["content"] == text

    def test_split_long_text_paragraphs(self):
        p1 = "Paragraph 1 with some content describing feature A."
        p2 = "Paragraph 2 describing feature B in deeper detail."
        p3 = "Paragraph 3 wrapping up the conclusions with actionable tips."
        text = f"{p1}\n\n{p2}\n\n{p3}"
        res = split_thread_engine(text, limit=70, numbering=True, numbering_format="fraction")
        assert res["total_posts"] >= 3
        for p in res["posts"]:
            assert p["is_valid"] is True
            assert f"/{res['total_posts']}" in p["content"]

    def test_split_numbering_formats(self):
        text = "Sentence one. " * 15
        res_thread = split_thread_engine(text, limit=100, numbering=True, numbering_format="fraction_thread")
        assert "🧵 1/" in res_thread["posts"][0]["content"]

        res_bracket = split_thread_engine(text, limit=100, numbering=True, numbering_format="bracket")
        assert "[1/" in res_bracket["posts"][0]["content"]

        res_counter = split_thread_engine(text, limit=100, numbering=True, numbering_format="counter")
        assert "1. " in res_counter["posts"][0]["content"]


class TestHookGeneratorEngine:
    def test_generate_hooks_default(self):
        res = generate_hooks_engine("Async Python", niche="software engineering", count=10)
        assert res["topic"] == "Async Python"
        assert len(res["hooks"]) == 10
        for h in res["hooks"]:
            assert "Async Python" in h["hook"]
            assert "framework" in h

    def test_generate_hooks_filtered_framework(self):
        res = generate_hooks_engine("AI Agents", framework="contrarian", count=3)
        assert len(res["hooks"]) == 3
        for h in res["hooks"]:
            assert h["framework"] == "contrarian"


class TestEngagementAnalyzerEngine:
    def test_analyze_empty_text(self):
        res = analyze_engagement_engine("")
        assert res["score"] == 0
        assert res["grade"] == "F"

    def test_analyze_high_quality_post(self):
        post = (
            "Most developers think building AI tools requires 50 npm packages.\n\n"
            "They are completely wrong.\n\n"
            "Here is how to build an MCP server in stdlib Python:\n"
            "- Pure JSON-RPC 2.0 loop\n"
            "- Zero external libraries\n"
            "- 5ms startup\n\n"
            "What is your favorite stdlib trick? Reply below 👇"
        )
        res = analyze_engagement_engine(post, platform="twitter")
        assert res["score"] >= 70
        assert res["grade"] in ("A+", "A", "B")
        assert res["metrics"]["has_cta"] is True
        assert res["metrics"]["is_within_limit"] is True


class TestMCPServerProtocol:
    @pytest.fixture
    def server(self):
        return MCPServer()

    def test_initialize(self, server):
        req = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05"},
        })
        resp_str = server.process_message(req)
        assert resp_str is not None
        resp = json.loads(resp_str)
        assert resp["id"] == 1
        assert resp["result"]["serverInfo"]["name"] == "omnipost-mcp-server"
        assert "tools" in resp["result"]["capabilities"]

    def test_ping(self, server):
        req = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "ping"})
        resp = json.loads(server.process_message(req))
        assert resp["id"] == 2
        assert resp["result"] == {}

    def test_notifications_initialized(self, server):
        req = json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"})
        resp = server.process_message(req)
        assert resp is None

    def test_tools_list(self, server):
        req = json.dumps({"jsonrpc": "2.0", "id": 3, "method": "tools/list"})
        resp = json.loads(server.process_message(req))
        tools = resp["result"]["tools"]
        tool_names = [t["name"] for t in tools]
        assert "omni_format_post" in tool_names
        assert "omni_split_thread" in tool_names
        assert "omni_generate_hooks" in tool_names
        assert "omni_analyze_engagement" in tool_names
        assert "omni_export_campaign" in tool_names
        assert "omni_get_diagnostics" in tool_names
        assert "omni_audit_accessibility" in tool_names
        assert len(tools) == 7

    def test_tool_call_audit_accessibility(self, server):
        req = json.dumps({
            "jsonrpc": "2.0",
            "id": 99,
            "method": "tools/call",
            "params": {
                "name": "omni_audit_accessibility",
                "arguments": {
                    "alt_text": "A colorful bar chart displaying user retention rate across 6 months.",
                    "post_text": "Spoiler alert! Here are the stats.",
                    "platform": "mastodon",
                },
            },
        })
        resp = json.loads(server.process_message(req))
        assert resp["id"] == 99
        assert resp["result"]["isError"] is False
        content = json.loads(resp["result"]["content"][0]["text"])
        assert content["platform"] == "mastodon"
        assert content["alt_evaluation"]["is_valid_length"] is True
        assert content["content_warning"]["needs_cw"] is True

    def test_tool_call_format_post(self, server):
        req = json.dumps({
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "omni_format_post",
                "arguments": {
                    "text": "Building in public today",
                    "platform": "twitter",
                    "style": "bold",
                    "hashtags": ["dev", "ai"],
                },
            },
        })
        resp = json.loads(server.process_message(req))
        assert resp["id"] == 4
        assert resp["result"]["isError"] is False
        content_text = resp["result"]["content"][0]["text"]
        data = json.loads(content_text)
        assert "𝗕𝘂𝗶𝗹𝗱𝗶𝗻𝗴" in data["text"]
        assert "#dev" in data["text"]

    def test_tool_call_split_thread(self, server):
        req = json.dumps({
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "omni_split_thread",
                "arguments": {
                    "text": "Post 1 paragraph.\n\nPost 2 paragraph.\n\nPost 3 paragraph.",
                    "limit": 25,
                },
            },
        })
        resp = json.loads(server.process_message(req))
        content = json.loads(resp["result"]["content"][0]["text"])
        assert content["total_posts"] >= 3

    def test_tool_call_generate_hooks(self, server):
        req = json.dumps({
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {
                "name": "omni_generate_hooks",
                "arguments": {"topic": "Developer Tooling", "count": 5},
            },
        })
        resp = json.loads(server.process_message(req))
        content = json.loads(resp["result"]["content"][0]["text"])
        assert len(content["hooks"]) == 5

    def test_tool_call_analyze_engagement(self, server):
        req = json.dumps({
            "jsonrpc": "2.0",
            "id": 7,
            "method": "tools/call",
            "params": {
                "name": "omni_analyze_engagement",
                "arguments": {"text": "Simple test tweet with a question? Comment below 👇"},
            },
        })
        resp = json.loads(server.process_message(req))
        content = json.loads(resp["result"]["content"][0]["text"])
        assert "score" in content
        assert "recommendations" in content

    def test_tool_call_export_campaign(self, server):
        sample = {
            "name": "MCP Campaign",
            "posts": [{"content": "Post 1", "platform": "twitter"}],
        }
        req = json.dumps({
            "jsonrpc": "2.0",
            "id": 8,
            "method": "tools/call",
            "params": {
                "name": "omni_export_campaign",
                "arguments": {"campaign": sample, "format": "json"},
            },
        })
        resp = json.loads(server.process_message(req))
        assert "MCP Campaign" in resp["result"]["content"][0]["text"]

    def test_tool_call_get_diagnostics(self, server):
        req = json.dumps({
            "jsonrpc": "2.0",
            "id": 9,
            "method": "tools/call",
            "params": {
                "name": "omni_get_diagnostics",
                "arguments": {"platform": "twitter"},
            },
        })
        resp = json.loads(server.process_message(req))
        content = json.loads(resp["result"]["content"][0]["text"])
        assert content["engine"] == "Omnipost Social Engine"
        assert "twitter" in content["platform_limits"]

    def test_tool_not_found(self, server):
        req = json.dumps({
            "jsonrpc": "2.0",
            "id": 10,
            "method": "tools/call",
            "params": {"name": "non_existent_tool"},
        })
        resp = json.loads(server.process_message(req))
        assert "error" in resp
        assert resp["error"]["code"] == -32601

    def test_invalid_json_parse_error(self, server):
        resp = json.loads(server.process_message("{invalid json"))
        assert resp["error"]["code"] == -32700


class TestClientConfigs:
    def test_get_client_configs(self):
        configs = get_client_configs()
        assert "claude_desktop" in configs
        assert "cursor" in configs
        assert "cline" in configs
        assert "zed" in configs

        claude = configs["claude_desktop"]["mcpServers"]["omnipost"]
        assert "command" in claude
        assert "args" in claude
        assert "-m" in claude["args"]
