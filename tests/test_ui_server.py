"""
Unit tests for Omnipost Studio UI Server and REST APIs in omnipost_social_engine.
"""

import json
import time
import urllib.error
import urllib.request
import pytest

from omnipost_social_engine.ui_server import OmnipostServer


@pytest.fixture(scope="module")
def running_server():
    """Start an OmnipostServer on an ephemeral port for testing and stop after tests."""
    server = OmnipostServer(host="127.0.0.1", port=0)
    server.start(background=True)
    # Give server a moment to bind and listen
    time.sleep(0.1)
    yield server
    server.stop()


class TestStudioServerEndpoints:
    def test_get_root_serves_html(self, running_server):
        req = urllib.request.Request(f"{running_server.url}/")
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            assert "text/html" in resp.headers.get("Content-Type", "")
            body = resp.read().decode("utf-8")
            assert "Omnipost" in body

    def test_get_api_health(self, running_server):
        req = urllib.request.Request(f"{running_server.url}/api/health")
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["status"] == "ok"
            assert data["service"] == "omnipost-studio"

    def test_get_api_mcp_config(self, running_server):
        req = urllib.request.Request(f"{running_server.url}/api/mcp/config")
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert "claude_desktop" in data
            assert "cursor" in data

    def test_get_api_diagnostics(self, running_server):
        req = urllib.request.Request(f"{running_server.url}/api/diagnostics?platform=twitter")
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["engine"] == "Omnipost Social Engine"
            assert "twitter" in data["platform_limits"]

    def test_get_api_hooks(self, running_server):
        req = urllib.request.Request(f"{running_server.url}/api/hooks?topic=DeveloperTools&count=4")
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert len(data["hooks"]) == 4

    def test_post_api_format(self, running_server):
        payload = json.dumps({
            "text": "Server format test",
            "platform": "twitter",
            "style": "bold",
            "hashtags": ["api"],
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{running_server.url}/api/format",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert "𝗦𝗲𝗿𝘃𝗲𝗿" in data["text"]
            assert data["is_valid"] is True

    def test_post_api_split(self, running_server):
        payload = json.dumps({
            "text": "Paragraph A.\n\nParagraph B.\n\nParagraph C.",
            "limit": 25,
            "numbering": True,
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{running_server.url}/api/split",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["total_posts"] >= 3

    def test_post_api_hooks(self, running_server):
        payload = json.dumps({
            "topic": "Python Performance",
            "niche": "backend",
            "count": 6,
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{running_server.url}/api/hooks",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert len(data["hooks"]) == 6

    def test_post_api_analyze(self, running_server):
        payload = json.dumps({
            "text": "Are you using Python stdlib? Let me know below 👇",
            "platform": "twitter",
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{running_server.url}/api/analyze",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert "score" in data
            assert data["metrics"]["has_cta"] is True

    def test_post_api_export(self, running_server):
        payload = json.dumps({
            "campaign": "sample",
            "format": "csv",
            "preset": "buffer",
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{running_server.url}/api/export",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert "Date,Text,Media,Campaign" in data["content"]

    def test_options_cors(self, running_server):
        req = urllib.request.Request(f"{running_server.url}/api/health", method="OPTIONS")
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 204
            assert resp.headers.get("Access-Control-Allow-Origin") == "*"

    def test_invalid_json_payload_returns_400(self, running_server):
        req = urllib.request.Request(
            f"{running_server.url}/api/format",
            data=b"invalid json bytes",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(req)
        assert exc_info.value.code == 400

    def test_not_found_endpoint_returns_404(self, running_server):
        req = urllib.request.Request(f"{running_server.url}/api/non_existent_route", method="POST")
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(req)
        assert exc_info.value.code == 404

    def test_get_api_accessibility(self, running_server):
        import urllib.parse
        q = urllib.parse.urlencode({"alt": "Diagram of neural network layers", "post": "Deep learning paper update"})
        req = urllib.request.Request(f"{running_server.url}/api/accessibility?{q}")
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["alt_evaluation"]["is_valid_length"] is True

    def test_post_api_accessibility(self, running_server):
        payload = json.dumps({
            "alt": "Photo of Mars rover landing.",
            "post": "Big news regarding the rover mission!",
            "platform": "bluesky",
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{running_server.url}/api/accessibility",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["cleaned_alt_text"] == "Mars rover landing."
            assert data["platform"] == "bluesky"
