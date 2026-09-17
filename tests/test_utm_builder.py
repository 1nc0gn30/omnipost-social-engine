"""Tests for UTM Builder, Link Attribution, Privacy Cleanser, and MCP Tools."""

import json
import urllib.parse
import pytest

from omnipost_social_engine.utm_builder import (
    UTMParameters,
    build_utm_url,
    build_platform_utm_url,
    sanitize_tracking_params,
    generate_campaign_links,
    tag_post_links,
    generate_vanity_redirect_html,
    PLATFORM_UTM_DEFAULTS,
    TRACKING_PARAMS_TO_STRIP,
)
from omnipost_social_engine.mcp_server import MCPServer
from omnipost_social_engine.cli import build_parser, main


def test_utm_parameters_dataclass():
    params = UTMParameters(
        base_url="https://example.com/product",
        utm_source="Twitter",
        utm_medium="Social_Post",
        utm_campaign="Spring_Sale",
        utm_term="ai tools",
        utm_content="variant_a",
        custom_params={"ref": "launch_banner"},
    )
    url = params.build_url()
    assert "utm_source=twitter" in url
    assert "utm_medium=social_post" in url
    assert "utm_campaign=spring_sale" in url
    assert "utm_term=ai+tools" in url or "utm_term=ai%20tools" in url
    assert "utm_content=variant_a" in url
    assert "ref=launch_banner" in url

    d = params.to_dict()
    assert d["base_url"] == "https://example.com/product"
    assert d["utm_source"] == "Twitter"
    assert d["utm_medium"] == "Social_Post"
    assert d["final_url"] == url


def test_sanitize_tracking_params():
    dirty_url = (
        "https://example.com/page?fbclid=IwAR123&gclid=Cj0K&utm_source=newsletter"
        "&utm_medium=email&utm_campaign=digest&msclkid=abc456&igshid=xyz789"
    )
    cleansed = sanitize_tracking_params(dirty_url, keep_utm=True)
    assert "fbclid" not in cleansed
    assert "gclid" not in cleansed
    assert "msclkid" not in cleansed
    assert "igshid" not in cleansed
    assert "utm_source=newsletter" in cleansed
    assert "utm_medium=email" in cleansed

    # Cleaned with keep_utm=False
    cleansed_no_utm = sanitize_tracking_params(dirty_url, keep_utm=False)
    assert "utm_source" not in cleansed_no_utm
    assert cleansed_no_utm == "https://example.com/page"


def test_build_utm_url():
    url = build_utm_url(
        base_url="https://myapp.dev/pricing?gclid=bad_tracker",
        source="ProductHunt",
        medium="Launch",
        campaign="V2_Release",
        term="developer",
    )
    assert "gclid" not in url
    assert "utm_source=producthunt" in url
    assert "utm_medium=launch" in url
    assert "utm_campaign=v2_release" in url
    assert "utm_term=developer" in url


def test_build_platform_utm_url():
    url_tw = build_platform_utm_url("https://site.org", "twitter", "summer_boost")
    assert "utm_source=twitter" in url_tw
    assert "utm_medium=social_post" in url_tw
    assert "utm_campaign=summer_boost" in url_tw

    url_li = build_platform_utm_url("https://site.org", "linkedin", "summer_boost")
    assert "utm_source=linkedin" in url_li
    assert "utm_medium=social_post" in url_li


def test_generate_campaign_links():
    links = generate_campaign_links(
        base_url="https://agency.co",
        campaign="black_friday",
        platforms=["twitter", "linkedin", "bluesky", "threads", "mastodon", "newsletter"],
    )
    assert len(links) == 6
    assert "utm_source=twitter" in links["twitter"]
    assert "utm_source=linkedin" in links["linkedin"]
    assert "utm_source=bluesky" in links["bluesky"]
    assert "utm_source=threads" in links["threads"]
    assert "utm_source=mastodon" in links["mastodon"]
    assert "utm_source=newsletter" in links["newsletter"]


def test_tag_post_links():
    post_text = (
        "Check out our new release at https://example.com/blog and explore documentation "
        "at https://example.com/docs!"
    )
    tagged = tag_post_links(post_text, platform="bluesky", campaign="v3_announcement")
    assert "https://example.com/blog?utm_source=bluesky&utm_medium=social_post&utm_campaign=v3_announcement" in tagged
    assert "https://example.com/docs?utm_source=bluesky&utm_medium=social_post&utm_campaign=v3_announcement" in tagged


def test_generate_vanity_redirect_html():
    html = generate_vanity_redirect_html(
        target_url="https://github.com/myorg/myrepo?utm_source=qr",
        title="My Cool Project",
        og_description="Open source devtools for engineers",
        og_image="https://example.com/og.png",
        delay_ms=1000,
    )
    assert "<!DOCTYPE html>" in html
    assert "<title>My Cool Project</title>" in html
    assert '<meta http-equiv="refresh" content="1; url=https://github.com/myorg/myrepo?utm_source=qr">' in html
    assert 'content="Open source devtools for engineers"' in html
    assert 'content="https://example.com/og.png"' in html
    assert "window.location.replace(" in html


def test_mcp_tools_utm():
    server = MCPServer()

    # omni_build_utm_url
    req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "omni_build_utm_url",
            "arguments": {
                "base_url": "https://test.io",
                "source": "mastodon",
                "medium": "social",
                "campaign": "launch",
            },
        },
    }
    resp = json.loads(server.process_message(json.dumps(req)))
    data = json.loads(resp["result"]["content"][0]["text"])
    assert data["source"] == "mastodon"
    assert "utm_source=mastodon" in data["final_url"]

    # omni_sanitize_url
    req_san = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "omni_sanitize_url",
            "arguments": {
                "url": "https://test.io?gclid=ad123&utm_source=promo",
                "keep_utm": True,
            },
        },
    }
    resp_san = json.loads(server.process_message(json.dumps(req_san)))
    data_san = json.loads(resp_san["result"]["content"][0]["text"])
    assert data_san["stripped"] is True
    assert "gclid" not in data_san["cleansed_url"]
    assert "utm_source=promo" in data_san["cleansed_url"]

    # omni_generate_campaign_links
    req_camp = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "omni_generate_campaign_links",
            "arguments": {
                "base_url": "https://test.io",
                "campaign": "festive",
                "platforms": ["twitter", "linkedin"],
            },
        },
    }
    resp_camp = json.loads(server.process_message(json.dumps(req_camp)))
    data_camp = json.loads(resp_camp["result"]["content"][0]["text"])
    assert "twitter" in data_camp["links"]
    assert "linkedin" in data_camp["links"]

    # omni_tag_post_links
    req_tag = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "omni_tag_post_links",
            "arguments": {
                "text": "Get it here: https://download.app",
                "platform": "twitter",
                "campaign": "promo",
            },
        },
    }
    resp_tag = json.loads(server.process_message(json.dumps(req_tag)))
    data_tag = json.loads(resp_tag["result"]["content"][0]["text"])
    assert "utm_source=twitter" in data_tag["tagged_text"]

    # omni_vanity_redirect
    req_van = {
        "jsonrpc": "2.0",
        "id": 5,
        "method": "tools/call",
        "params": {
            "name": "omni_vanity_redirect",
            "arguments": {
                "target_url": "https://landing.app",
                "title": "Welcome Page",
            },
        },
    }
    resp_van = json.loads(server.process_message(json.dumps(req_van)))
    html_out = resp_van["result"]["content"][0]["text"]
    assert "<!DOCTYPE html>" in html_out
    assert "Welcome Page" in html_out


def test_cli_utm(capsys):
    # Test build single URL
    rc = main(["utm", "--url", "https://mysite.com", "--campaign", "v4", "--platform", "threads"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "utm_source=threads" in captured.out

    # Test sanitize
    rc = main(["utm", "--url", "https://mysite.com?fbclid=xyz", "--sanitize", "--json"])
    assert rc == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["stripped"] is True
    assert "fbclid" not in data["cleansed_url"]

    # Test campaign-links
    rc = main(["utm", "--url", "https://mysite.com", "--campaign", "winter", "--campaign-links", "--json"])
    assert rc == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "twitter" in data["links"]
