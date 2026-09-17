"""
Omnipost Social Engine - Command Line Interface (CLI)
Multi-command CLI for formatting, thread splitting, viral hook generation,
engagement analysis, campaign exporting, MCP server hosting, and diagnostics.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional

from .campaign_exporter import PLATFORM_LIMITS, CampaignExporter
from .mcp_server import (
    UNICODE_MAPS,
    MCPServer,
    analyze_engagement_engine,
    format_post_engine,
    generate_hooks_engine,
    get_client_configs,
    get_diagnostics_engine,
    run_mcp_server,
    split_thread_engine,
)
from .ui_server import run_server
from .accessibility_synthesizer import evaluate_accessibility_suite
from .utm_builder import (
    build_utm_url,
    build_platform_utm_url,
    sanitize_tracking_params,
    generate_campaign_links,
    tag_post_links,
    generate_vanity_redirect_html,
)


# Terminal Color Helpers
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"
    RESET = "\033[0m"

    @classmethod
    def strip_if_no_color(cls, text: str) -> str:
        """Strip ANSI escape codes if NO_COLOR is set or stdout is not a TTY."""
        if os.environ.get("NO_COLOR") or not sys.stdout.isatty():
            import re
            return re.sub(r"\033\[[0-9;]*m", "", text)
        return text


def colorize(text: str, color_code: str) -> str:
    """Wrap text in ANSI color code with safety check."""
    if os.environ.get("NO_COLOR") or not sys.stdout.isatty():
        return text
    return f"{color_code}{text}{Colors.RESET}"


def read_text_or_file(input_val: str) -> str:
    """
    Read text either directly from the argument string, from a local file,
    or from standard input if input_val is '-' or points to an existing file.
    """
    if input_val == "-":
        return sys.stdin.read()

    if os.path.isfile(input_val):
        with open(input_val, "r", encoding="utf-8") as f:
            return f.read()

    return input_val


def print_banner() -> None:
    """Print the Omnipost CLI banner."""
    banner = f"""
{Colors.BOLD}{Colors.CYAN}╭─────────────────────────────────────────────────────────────╮
│  ✨ OMNIPOST SOCIAL ENGINE                                 │
│  Multi-Platform Copywriter, Thread Splitter & MCP Server    │
╰─────────────────────────────────────────────────────────────╯{Colors.RESET}
"""
    print(Colors.strip_if_no_color(banner))


# Subcommand Handlers
def cmd_serve(args: argparse.Namespace) -> int:
    """Run the Omnipost Studio web interface."""
    host = args.host
    port = args.port
    open_browser = getattr(args, "open", False)
    run_server(host=host, port=port, open_browser=open_browser)
    return 0


def cmd_format(args: argparse.Namespace) -> int:
    """Format and style social media posts."""
    raw_input = read_text_or_file(args.input)
    hashtags = args.tags.split(",") if args.tags else None
    
    res = format_post_engine(
        text=raw_input,
        platform=args.platform,
        style=args.style,
        hashtags=hashtags,
        trim=not args.no_trim,
    )

    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return 0

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(res["text"])
        print(colorize(f"✅ Formatted post written to: {args.out}", Colors.GREEN))
        return 0

    status_color = Colors.GREEN if res["is_valid"] else Colors.RED
    status_label = "VALID" if res["is_valid"] else f"EXCEEDS LIMIT by {-res['remaining_chars']} chars"

    print(f"\n{Colors.BOLD}Platform:{Colors.RESET} {res['platform_name']}")
    print(f"{Colors.BOLD}Character Count:{Colors.RESET} {res['char_count']} / {res['char_limit']} ({colorize(status_label, status_color)})")
    print(f"{Colors.BOLD}Word Count:{Colors.RESET} {res['word_count']}")
    if res["style"] != "normal":
        print(f"{Colors.BOLD}Typography Style:{Colors.RESET} {res['style']}")
    print(f"\n{Colors.CYAN}{'─' * 50}{Colors.RESET}")
    print(res["text"])
    print(f"{Colors.CYAN}{'─' * 50}{Colors.RESET}\n")

    return 0 if res["is_valid"] else 1


def cmd_split(args: argparse.Namespace) -> int:
    """Split long text into platform-optimized threads."""
    raw_input = read_text_or_file(args.input)
    res = split_thread_engine(
        text=raw_input,
        limit=args.limit,
        platform=args.platform,
        numbering=not args.no_numbering,
        numbering_format=args.numbering_format,
    )

    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return 0

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            for p in res["posts"]:
                f.write(p["content"] + "\n\n---\n\n")
        print(colorize(f"✅ Generated {res['total_posts']} thread posts saved to: {args.out}", Colors.GREEN))
        return 0

    print(f"\n{Colors.BOLD}🧵 Thread Split Results:{Colors.RESET} {res['total_posts']} Posts (Limit: {res['char_limit']} chars)")
    print(f"{Colors.CYAN}{'═' * 60}{Colors.RESET}")

    for p in res["posts"]:
        status_color = Colors.GREEN if p["is_valid"] else Colors.RED
        print(f"{Colors.BOLD}[Post {p['index']}/{p['total']}]{Colors.RESET} ({p['char_count']}/{p['char_limit']} chars - {colorize('OK' if p['is_valid'] else 'EXCEEDS', status_color)})")
        print(f"{Colors.DIM}{'─' * 40}{Colors.RESET}")
        print(p["content"])
        print()

    return 0


def cmd_hooks(args: argparse.Namespace) -> int:
    """Generate high-converting viral hooks and headlines."""
    res = generate_hooks_engine(
        topic=args.topic,
        niche=args.niche,
        framework=args.framework,
        count=args.count,
    )

    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return 0

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            for h in res["hooks"]:
                f.write(f"[{h['framework'].upper()}]\n{h['hook']}\n\n")
        print(colorize(f"✅ Generated {len(res['hooks'])} viral hooks saved to: {args.out}", Colors.GREEN))
        return 0

    print(f"\n{Colors.BOLD}⚡ Viral Hooks for:{Colors.RESET} '{res['topic']}' (Niche: {res['niche']})")
    print(f"{Colors.CYAN}{'═' * 60}{Colors.RESET}\n")

    for h in res["hooks"]:
        print(f"{Colors.BOLD}{Colors.YELLOW}[{h['framework'].upper()}]{Colors.RESET} ({h['char_count']} chars)")
        print(f"{h['hook']}\n")

    return 0


def cmd_analyze(args: argparse.Namespace) -> int:
    """Score engagement potential and readability."""
    raw_input = read_text_or_file(args.input)
    res = analyze_engagement_engine(text=raw_input, platform=args.platform)

    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return 0

    score = res["score"]
    score_color = Colors.GREEN if score >= 75 else (Colors.YELLOW if score >= 50 else Colors.RED)

    print(f"\n{Colors.BOLD}📊 Social Engagement Score:{Colors.RESET} {colorize(f'{score} / 100', score_color)} ({res['grade']} - {res['viral_readiness']})")
    print(f"{Colors.CYAN}{'─' * 60}{Colors.RESET}")

    m = res["metrics"]
    print(f"{Colors.BOLD}Metrics:{Colors.RESET}")
    print(f"  • Characters: {m['char_count']} / {m['char_limit']} ({'Within limit' if m['is_within_limit'] else 'OVER LIMIT'})")
    print(f"  • Words: {m['word_count']} | Lines: {m['line_count']} | Reading Time: ~{m['reading_time_sec']}s")
    print(f"  • Flesch Reading Ease: {m['flesch_reading_ease']} | Grade Level: {m['reading_grade_level']}")
    print(f"  • Power Words: {m['power_words_count']} | Emojis: {m['emoji_count']} | CTA Detected: {'Yes' if m['has_cta'] else 'No'}")

    b = res["breakdown"]
    print(f"\n{Colors.BOLD}Score Breakdown:{Colors.RESET}")
    print(f"  • Hook Strength: {b['hook_strength']} / 40")
    print(f"  • Formatting & Scannability: {b['formatting']} / 30")
    print(f"  • Call To Action: {b['cta_engagement']} / 20")
    print(f"  • Readability Index: {b['readability']} / 20")

    print(f"\n{Colors.BOLD}Actionable Recommendations:{Colors.RESET}")
    for tip in res["recommendations"]:
        print(f"  💡 {tip}")
    print()

    return 0


def cmd_export(args: argparse.Namespace) -> int:
    """Export campaign schedule to CSV, JSON, Markdown, or Raw text."""
    camp = CampaignExporter.parse_campaign(args.file)
    content = CampaignExporter.export(
        camp,
        format=args.format,
        preset=args.preset,
        view=args.view,
    )

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(content)
        print(colorize(f"✅ Campaign exported ({args.format.upper()}) to: {args.out}", Colors.GREEN))
        return 0

    print(content)
    return 0


def cmd_accessibility(args: argparse.Namespace) -> int:
    """Audit alt-text accessibility and check for Content Warning (CW) triggers."""
    alt_text = read_text_or_file(args.alt) if getattr(args, "alt", None) else ""
    post_text = read_text_or_file(args.post) if getattr(args, "post", None) else ""
    platform = getattr(args, "platform", "twitter") or "twitter"
    res = evaluate_accessibility_suite(alt_text=alt_text, post_text=post_text, platform=platform)

    if getattr(args, "json", False):
        print(json.dumps(res, indent=2))
        return 0

    print_banner()
    print(f"{Colors.BOLD}Accessibility & Content Warning Audit [{platform.upper()}]:{Colors.RESET}\n")

    if alt_text:
        eval_data = res["alt_evaluation"]
        grade_color = Colors.GREEN if eval_data["grade"] in ("AAA", "AA") else (Colors.YELLOW if eval_data["grade"] == "A" else Colors.RED)
        print(f"  {Colors.BOLD}Alt-Text Quality Score:{Colors.RESET} {grade_color}{eval_data['descriptive_quality_score']}/100 ({eval_data['grade']}){Colors.RESET}")
        print(f"  • Length: {eval_data['char_count']}/{eval_data['char_limit']} chars ({'Valid' if eval_data['is_valid_length'] else 'Exceeds limit'})")
        if eval_data["has_redundant_intro"]:
            print(f"  • {Colors.YELLOW}Warning:{Colors.RESET} Contains redundant prefix ('{eval_data['detected_redundancy']}').")
            if res.get("cleaned_alt_text"):
                print(f"    Suggested clean: \"{res['cleaned_alt_text']}\"")
        if eval_data["recommendations"]:
            print(f"  • Recommendations:")
            for rec in eval_data["recommendations"]:
                print(f"    - {rec}")
    else:
        print(f"  {Colors.YELLOW}No alt-text provided for audit.{Colors.RESET}")

    print()
    cw_data = res["content_warning"]
    if cw_data["needs_cw"]:
        print(f"  {Colors.BOLD}Content Warning (CW) Needed:{Colors.RESET} {Colors.YELLOW}YES{Colors.RESET}")
        print(f"  • Trigger Categories: {', '.join(cw_data['categories_detected'])}")
        print(f"  • Suggested Label: {Colors.BOLD}{cw_data['suggested_warning_label']}{Colors.RESET}")
        if cw_data.get("formatted_mastodon_post"):
            print(f"  • Mastodon formatted:\n    {cw_data['formatted_mastodon_post']}")
    else:
        print(f"  {Colors.BOLD}Content Warning:{Colors.RESET} {Colors.GREEN}No sensitive triggers detected.{Colors.RESET}")
    print()
    return 0


def cmd_mcp(args: argparse.Namespace) -> int:
    """Run Model Context Protocol (MCP) server over stdio."""
    run_mcp_server()
    return 0


def cmd_mcp_config(args: argparse.Namespace) -> int:
    """Output drop-in MCP client configurations for Claude Desktop, Cursor, Cline, Zed."""
    configs = get_client_configs()
    client = getattr(args, "client", "all").lower()

    if client == "all":
        print(json.dumps(configs, indent=2))
    elif client in ("claude", "claude_desktop"):
        print(json.dumps(configs["claude_desktop"], indent=2))
    elif client == "cursor":
        print(json.dumps(configs["cursor"], indent=2))
    elif client == "cline":
        print(json.dumps(configs["cline"], indent=2))
    elif client == "zed":
        print(json.dumps(configs["zed"], indent=2))
    else:
        print(colorize(f"Unknown client '{client}'. Choose from 'claude', 'cursor', 'cline', 'zed', 'all'.", Colors.RED))
        return 1
    return 0


def cmd_platform(args: argparse.Namespace) -> int:
    """Display multi-OS diagnostics and platform character limits."""
    diag = get_diagnostics_engine(args.platform)
    if args.json:
        print(json.dumps(diag, indent=2))
        return 0

    print_banner()
    print(f"{Colors.BOLD}System Diagnostics:{Colors.RESET}")
    print(f"  • Engine Version: {diag['version']}")
    print(f"  • Python Version: {diag['python_version']}")
    print(f"  • Operating System: {diag['os']} ({diag['os_release']} - {diag['architecture']})")
    print(f"  • Terminal Encoding: {diag['unicode_support']}")
    print(f"  • Available Styles: {', '.join(diag['available_unicode_styles'])}")

    print(f"\n{Colors.BOLD}Platform Character & Media Specifications:{Colors.RESET}")
    print(f"{Colors.CYAN}{'─' * 60}{Colors.RESET}")
    for p_id, p_info in diag["platform_limits"].items():
        print(f"  {Colors.BOLD}{p_info['name']}{Colors.RESET} ({p_id}):")
        print(f"    - Char Limit: {p_info['char_limit']}")
        print(f"    - Media Limit: {p_info['media_limit']} items")
        print(f"    - Thread Support: {'Yes' if p_info.get('thread_supported') else 'No'}")
        print(f"    - Recommended Hashtags: ~{p_info.get('hashtag_recommended', 2)}")
    print()
    return 0


def cmd_utm(args: argparse.Namespace) -> int:
    """Build, sanitize, or generate UTM campaign URLs and vanity redirects."""
    url = getattr(args, "url", None)
    if args.sanitize:
        if not url:
            print(colorize("Error: --url is required for --sanitize", Colors.RED), file=sys.stderr)
            return 1
        clean_url = sanitize_tracking_params(url, keep_utm=not args.strip_all)
        if args.json:
            print(json.dumps({"original_url": url, "cleansed_url": clean_url, "stripped": url != clean_url}, indent=2))
        else:
            print(clean_url)
        return 0

    if args.campaign_links:
        if not url or not args.campaign:
            print(colorize("Error: --url and --campaign are required for --campaign-links", Colors.RED), file=sys.stderr)
            return 1
        platforms = args.platforms.split(",") if getattr(args, "platforms", None) else None
        links = generate_campaign_links(url, campaign=args.campaign, platforms=platforms, content=args.content)
        if args.json:
            print(json.dumps({"base_url": url, "campaign": args.campaign, "links": links}, indent=2))
        else:
            print(f"{Colors.BOLD}Campaign Links ({args.campaign}):{Colors.RESET}")
            for p, u in links.items():
                print(f"  • {p:<12}: {u}")
        return 0

    if args.tag_post:
        post_content = read_text_or_file(args.tag_post)
        if not args.campaign:
            print(colorize("Error: --campaign is required for --tag-post", Colors.RED), file=sys.stderr)
            return 1
        platform = args.platform or "twitter"
        tagged = tag_post_links(post_content, platform=platform, campaign=args.campaign, content=args.content)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(tagged)
            print(f"Tagged post saved to {args.out}")
        else:
            print(tagged)
        return 0

    if args.vanity:
        if not url:
            print(colorize("Error: --url is required for --vanity", Colors.RED), file=sys.stderr)
            return 1
        title = args.title or "Redirecting..."
        html_code = generate_vanity_redirect_html(
            target_url=url,
            title=title,
            og_description=args.description,
            og_image=args.image,
            delay_ms=args.delay or 0,
        )
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(html_code)
            print(f"Vanity redirect page saved to {args.out}")
        else:
            print(html_code)
        return 0

    # Default: build single UTM URL
    if not url:
        print(colorize("Error: --url is required to build a UTM link", Colors.RED), file=sys.stderr)
        return 1

    campaign = args.campaign or "launch"
    if args.platform:
        final_url = build_platform_utm_url(
            base_url=url,
            platform=args.platform,
            campaign=campaign,
            content=args.content,
            term=args.term,
        )
    else:
        source = args.source or "social"
        medium = args.medium or "post"
        final_url = build_utm_url(
            base_url=url,
            source=source,
            medium=medium,
            campaign=campaign,
            content=args.content,
            term=args.term,
        )

    if args.json:
        res = {
            "base_url": url,
            "campaign": campaign,
            "final_url": final_url,
        }
        if args.platform:
            res["platform"] = args.platform
        print(json.dumps(res, indent=2))
    elif args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(final_url + "\n")
        print(f"Tracked URL saved to {args.out}")
    else:
        print(final_url)
    return 0


def cmd_test(args: argparse.Namespace) -> int:
    """Run test suite."""
    import unittest
    # Try running pytest if available, else unittest
    try:
        import pytest
        ret = pytest.main(["-v", "tests"])
        return int(ret)
    except ImportError:
        loader = unittest.TestLoader()
        suite = loader.discover("tests")
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        return 0 if result.wasSuccessful() else 1


def build_parser() -> argparse.ArgumentParser:
    """Construct CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="omnipost",
        description="Omnipost Social Engine: Pure-Python social automation, MCP server, and Studio.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-v", "--version", action="version", version="omnipost-social-engine 1.0.0")

    subparsers = parser.add_subparsers(dest="subcommand", help="Available subcommands")

    # serve
    p_serve = subparsers.add_parser("serve", help="Start Omnipost Material 3 Studio web UI")
    p_serve.add_argument("--port", type=int, default=8086, help="Port to bind (default: 8086)")
    p_serve.add_argument("--host", default="0.0.0.0", help="Host interface (default: 0.0.0.0)")
    p_serve.add_argument("--open", action="store_true", help="Automatically open browser")
    p_serve.set_defaults(func=cmd_serve)

    # format
    p_format = subparsers.add_parser("format", help="Format and style a social post")
    p_format.add_argument("input", help="Text content or path to text file ('-' for stdin)")
    p_format.add_argument(
        "--platform", "-p",
        default="twitter",
        choices=["twitter", "linkedin", "bluesky", "threads", "mastodon", "facebook", "instagram"],
        help="Target platform (default: twitter)",
    )
    p_format.add_argument(
        "--style", "-s",
        default="normal",
        choices=["normal", "bold", "italic", "bold_italic", "monospace", "script", "double_struck", "sans", "underline", "strikethrough"],
        help="Unicode font style",
    )
    p_format.add_argument("--tags", "-t", help="Comma-separated hashtags to append")
    p_format.add_argument("--no-trim", action="store_true", help="Preserve whitespace")
    p_format.add_argument("--out", "-o", help="Write output to file")
    p_format.add_argument("--json", action="store_true", help="Output raw JSON")
    p_format.set_defaults(func=cmd_format)

    # split
    p_split = subparsers.add_parser("split", help="Split long copy into a thread")
    p_split.add_argument("input", help="Text content or path to text file ('-' for stdin)")
    p_split.add_argument("--limit", "-l", type=int, default=280, help="Character limit per post (default: 280)")
    p_split.add_argument("--platform", "-p", default="twitter", help="Target platform")
    p_split.add_argument("--no-numbering", action="store_true", help="Disable (1/N) thread numbering")
    p_split.add_argument(
        "--numbering-format",
        default="fraction",
        choices=["fraction", "fraction_thread", "bracket", "counter"],
        help="Numbering format",
    )
    p_split.add_argument("--out", "-o", help="Write output to file")
    p_split.add_argument("--json", action="store_true", help="Output raw JSON")
    p_split.set_defaults(func=cmd_split)

    # hooks
    p_hooks = subparsers.add_parser("hooks", help="Generate viral copywriting hooks")
    p_hooks.add_argument("topic", help="Topic or product concept")
    p_hooks.add_argument("--niche", "-n", default="tech", help="Target audience/niche")
    p_hooks.add_argument(
        "--framework", "-f",
        default="all",
        choices=["all", "contrarian", "question", "number_list", "curiosity_gap", "transformation", "how_to", "negative_bias", "secret_mistake", "story_lead"],
        help="Copywriting framework",
    )
    p_hooks.add_argument("--count", "-c", type=int, default=10, help="Number of hooks to generate (default: 10)")
    p_hooks.add_argument("--out", "-o", help="Write output to file")
    p_hooks.add_argument("--json", action="store_true", help="Output raw JSON")
    p_hooks.set_defaults(func=cmd_hooks)

    # analyze
    p_analyze = subparsers.add_parser("analyze", help="Score engagement and readability")
    p_analyze.add_argument("input", help="Text content or path to text file ('-' for stdin)")
    p_analyze.add_argument("--platform", "-p", default="twitter", help="Target platform")
    p_analyze.add_argument("--json", action="store_true", help="Output raw JSON")
    p_analyze.set_defaults(func=cmd_analyze)

    # export
    p_export = subparsers.add_parser("export", help="Export campaign schedule to CSV/JSON/Markdown")
    p_export.add_argument("file", help="Campaign JSON/text file to export")
    p_export.add_argument(
        "--format", "-f",
        default="json",
        choices=["json", "csv", "markdown", "md", "txt", "raw"],
        help="Export format",
    )
    p_export.add_argument(
        "--preset",
        default="buffer",
        choices=["buffer", "hootsuite", "typefully", "generic"],
        help="CSV platform preset",
    )
    p_export.add_argument(
        "--view",
        default="calendar",
        choices=["calendar", "table", "cards", "checklist"],
        help="Markdown view style",
    )
    p_export.add_argument("--out", "-o", help="Write output to file")
    p_export.set_defaults(func=cmd_export)

    # accessibility / a11y
    p_a11y = subparsers.add_parser("accessibility", aliases=["a11y"], help="Audit alt-text accessibility and content warnings")
    p_a11y.add_argument("--alt", "-a", help="Alt-text string or file to audit")
    p_a11y.add_argument("--post", "-p", help="Post content string or file to scan for CWs")
    p_a11y.add_argument("--platform", default="twitter", help="Target platform (twitter, bluesky, mastodon, threads, linkedin)")
    p_a11y.add_argument("--json", action="store_true", help="Output raw JSON")
    p_a11y.set_defaults(func=cmd_accessibility)

    # mcp
    p_mcp = subparsers.add_parser("mcp", help="Run stdio Model Context Protocol (MCP) server")
    p_mcp.set_defaults(func=cmd_mcp)

    # mcp-config
    p_mcp_cfg = subparsers.add_parser("mcp-config", help="Print MCP server client configurations")
    p_mcp_cfg.add_argument("--client", "-c", default="all", choices=["claude", "cursor", "cline", "zed", "all"], help="Target client")
    p_mcp_cfg.set_defaults(func=cmd_mcp_config)

    # platform / diagnostics
    p_diag = subparsers.add_parser("platform", help="Display platform specs and diagnostics")
    p_diag.add_argument("--platform", "-p", help="Filter by specific platform")
    p_diag.add_argument("--json", action="store_true", help="Output raw JSON")
    p_diag.set_defaults(func=cmd_platform)

    p_diag_alias = subparsers.add_parser("diagnostics", help="Alias for platform diagnostics")
    p_diag_alias.add_argument("--platform", "-p", help="Filter by specific platform")
    p_diag_alias.add_argument("--json", action="store_true", help="Output raw JSON")
    p_diag_alias.set_defaults(func=cmd_platform)

    # utm
    p_utm = subparsers.add_parser("utm", help="Build, sanitize, or generate UTM campaign URLs and vanity redirects")
    p_utm.add_argument("--url", "-u", help="Destination base URL")
    p_utm.add_argument("--campaign", "-c", default="launch", help="Campaign identifier (e.g. spring_sale, launch)")
    p_utm.add_argument("--source", "-s", help="UTM source (e.g. twitter, linkedin, newsletter)")
    p_utm.add_argument("--medium", "-m", help="UTM medium (e.g. social_post, email, banner)")
    p_utm.add_argument("--term", help="UTM term / keyword")
    p_utm.add_argument("--content", help="UTM content variation")
    p_utm.add_argument("--platform", "-p", help="Target platform (auto-populates source and medium)")
    p_utm.add_argument("--sanitize", action="store_true", help="Strip invasive surveillance tracking IDs from --url")
    p_utm.add_argument("--strip-all", action="store_true", help="Strip both ad network IDs and UTM tags when sanitizing")
    p_utm.add_argument("--campaign-links", action="store_true", help="Generate tracked URLs for all platforms")
    p_utm.add_argument("--platforms", help="Comma-separated platforms for --campaign-links")
    p_utm.add_argument("--tag-post", help="File or text string to auto-tag bare URLs within post body")
    p_utm.add_argument("--vanity", action="store_true", help="Generate standalone HTML vanity redirect landing page")
    p_utm.add_argument("--title", help="Title for vanity redirect page")
    p_utm.add_argument("--description", help="OG description for vanity page")
    p_utm.add_argument("--image", help="OG image URL for vanity page")
    p_utm.add_argument("--delay", type=int, default=0, help="Delay in ms before redirecting")
    p_utm.add_argument("--out", "-o", help="Write output to file")
    p_utm.add_argument("--json", action="store_true", help="Output raw JSON")
    p_utm.set_defaults(func=cmd_utm)

    # test
    p_test = subparsers.add_parser("test", help="Run test suite")
    p_test.set_defaults(func=cmd_test)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Main CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.subcommand:
        print_banner()
        parser.print_help()
        return 0

    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\nAborted by user.")
        return 130
    except Exception as e:
        print(colorize(f"\n❌ Error: {str(e)}", Colors.RED), file=sys.stderr)
        if os.environ.get("OMNIPOST_DEBUG"):
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
