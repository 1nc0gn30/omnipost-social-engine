"""
Omnipost Social Engine
Zero-dependency, multi-platform social copywriting, thread splitting, campaign exporting,
and stdio Model Context Protocol (MCP) server for modern AI workflows.
"""

from .campaign_exporter import (
    PLATFORM_LIMITS,
    Campaign,
    CampaignExporter,
    Post,
)
from .cli import main
from .mcp_server import (
    UNICODE_MAPS,
    MCPServer,
    analyze_engagement_engine,
    apply_unicode_style,
    format_post_engine,
    generate_hooks_engine,
    get_client_configs,
    get_diagnostics_engine,
    run_mcp_server,
    split_thread_engine,
)
from .ui_server import (
    OmnipostServer,
    run_server,
)
from .schedule_planner import (
    PlatformPeakSlot,
    ScheduledPostSlot,
    HashtagAnalysisResult,
    get_peak_engagement_matrix,
    plan_campaign_schedule,
    analyze_hashtag_strategy,
)
from .accessibility_synthesizer import (
    AltTextEvaluation,
    ContentWarningSuggestion,
    AltTextSynthesizer,
    evaluate_accessibility_suite,
)
from .utm_builder import (
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

# Granular engines if available
try:
    from .formatter import SocialFormatter, EngagementAnalyzer, FormatResult
except ImportError:
    pass

try:
    from .thread_splitter import ThreadSplitter, ThreadResult, ThreadPost, NumberingStyle
except ImportError:
    pass

try:
    from .hook_generator import HookGenerator, HookFormula, HookResult
except ImportError:
    pass

# Friendly aliases
format_post = format_post_engine
split_thread = split_thread_engine
generate_hooks = generate_hooks_engine
analyze_engagement = analyze_engagement_engine
get_diagnostics = get_diagnostics_engine

__version__ = "1.0.0"
__author__ = "Omnipost Contributors"
__all__ = [
    "__version__",
    "PLATFORM_LIMITS",
    "Campaign",
    "Post",
    "CampaignExporter",
    "MCPServer",
    "run_mcp_server",
    "get_client_configs",
    "UNICODE_MAPS",
    "apply_unicode_style",
    "format_post_engine",
    "format_post",
    "split_thread_engine",
    "split_thread",
    "generate_hooks_engine",
    "generate_hooks",
    "analyze_engagement_engine",
    "analyze_engagement",
    "get_diagnostics_engine",
    "get_diagnostics",
    "OmnipostServer",
    "run_server",
    "main",
    "PlatformPeakSlot",
    "ScheduledPostSlot",
    "HashtagAnalysisResult",
    "get_peak_engagement_matrix",
    "plan_campaign_schedule",
    "analyze_hashtag_strategy",
    "AltTextEvaluation",
    "ContentWarningSuggestion",
    "AltTextSynthesizer",
    "evaluate_accessibility_suite",
    "UTMParameters",
    "build_utm_url",
    "build_platform_utm_url",
    "sanitize_tracking_params",
    "generate_campaign_links",
    "tag_post_links",
    "generate_vanity_redirect_html",
    "PLATFORM_UTM_DEFAULTS",
    "TRACKING_PARAMS_TO_STRIP",
]
