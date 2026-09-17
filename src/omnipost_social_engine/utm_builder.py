"""UTM Link Attribution, Campaign Tracking & Privacy Cleanser Engine.

Provides zero-dependency URL tracking parameter builder, surveillance tracker stripping,
multi-platform campaign link generator, in-copy URL auto-tagging, and vanity redirector generator.
100% Python Standard Library.
"""

from __future__ import annotations

import html
import json
import re
import urllib.parse
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Union

# Surveillance and ad tracking query parameters commonly injected by platforms
TRACKING_PARAMS_TO_STRIP: Set[str] = {
    # Facebook / Meta
    "fbclid",
    # Google / AdWords
    "gclid",
    "gclsrc",
    "dclid",
    "wbraid",
    "gbraid",
    # Microsoft / Bing
    "msclkid",
    # Twitter / X
    "twclid",
    "ref_src",
    "ref_url",
    # Instagram
    "igshid",
    # TikTok
    "ttclid",
    # Mailchimp
    "mc_cid",
    "mc_eid",
    # HubSpot
    "_hsenc",
    "_hsmi",
    # Spotify / YouTube share IDs
    "si",
    "spm",
    # Other ad networks
    "wickedid",
    "sc_campaign",
    "vero_id",
    "s_cid",
    "zanpid",
}

# Standard UTM parameter keys
UTM_KEYS: Set[str] = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
}

# Platform standard source & medium defaults
PLATFORM_UTM_DEFAULTS: Dict[str, Dict[str, str]] = {
    "twitter": {"source": "twitter", "medium": "social_post"},
    "x": {"source": "twitter", "medium": "social_post"},
    "linkedin": {"source": "linkedin", "medium": "social_post"},
    "bluesky": {"source": "bluesky", "medium": "social_post"},
    "bsky": {"source": "bluesky", "medium": "social_post"},
    "threads": {"source": "threads", "medium": "social_post"},
    "mastodon": {"source": "mastodon", "medium": "social_post"},
    "youtube": {"source": "youtube", "medium": "video_description"},
    "reddit": {"source": "reddit", "medium": "community_post"},
    "newsletter": {"source": "newsletter", "medium": "email"},
    "producthunt": {"source": "producthunt", "medium": "launch"},
    "github": {"source": "github", "medium": "readme"},
}

URL_REGEX = re.compile(
    r"https?://(?:[a-zA-Z0-9\-._~:/?#\[\]@!$&'()*+,;=]|%[0-9a-fA-F]{2})+"
)


@dataclass
class UTMParameters:
    """Dataclass holding structured UTM tracking parameters."""
    base_url: str
    utm_source: str
    utm_medium: str
    utm_campaign: str
    utm_term: Optional[str] = None
    utm_content: Optional[str] = None
    custom_params: Dict[str, str] = field(default_factory=dict)

    def build_url(self) -> str:
        """Construct the complete URL with normalized and properly encoded parameters."""
        parsed = urllib.parse.urlsplit(self.base_url)
        existing_params = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        
        # Strip old UTM keys to avoid duplicates
        filtered_params = [(k, v) for k, v in existing_params if k not in UTM_KEYS]
        
        new_params = list(filtered_params)
        if self.utm_source:
            new_params.append(("utm_source", self.utm_source.strip().lower()))
        if self.utm_medium:
            new_params.append(("utm_medium", self.utm_medium.strip().lower()))
        if self.utm_campaign:
            new_params.append(("utm_campaign", self.utm_campaign.strip().lower()))
        if self.utm_term:
            new_params.append(("utm_term", self.utm_term.strip()))
        if self.utm_content:
            new_params.append(("utm_content", self.utm_content.strip()))

        for k, v in self.custom_params.items():
            if k and v:
                new_params.append((k.strip(), str(v).strip()))

        encoded_query = urllib.parse.urlencode(new_params)
        return urllib.parse.urlunsplit((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            encoded_query,
            parsed.fragment,
        ))

    def to_dict(self) -> Dict[str, Any]:
        """Serialize parameters to dictionary representation."""
        d = {
            "base_url": self.base_url,
            "utm_source": self.utm_source,
            "utm_medium": self.utm_medium,
            "utm_campaign": self.utm_campaign,
            "final_url": self.build_url(),
        }
        if self.utm_term:
            d["utm_term"] = self.utm_term
        if self.utm_content:
            d["utm_content"] = self.utm_content
        if self.custom_params:
            d["custom_params"] = self.custom_params
        return d


def sanitize_tracking_params(url: str, keep_utm: bool = True) -> str:
    """Strip surveillance / ad network click identifiers from URL.
    
    Removes fbclid, gclid, msclkid, twclid, etc., while optionally
    preserving clean marketing UTM parameters.
    """
    if not url or not isinstance(url, str):
        return url

    parsed = urllib.parse.urlsplit(url.strip())
    if not parsed.query:
        return url

    params = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    kept_params = []

    for k, v in params:
        k_lower = k.lower()
        if k_lower in TRACKING_PARAMS_TO_STRIP:
            continue
        if not keep_utm and k_lower in UTM_KEYS:
            continue
        kept_params.append((k, v))

    new_query = urllib.parse.urlencode(kept_params)
    return urllib.parse.urlunsplit((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        new_query,
        parsed.fragment,
    ))


def build_utm_url(
    base_url: str,
    source: str,
    medium: str,
    campaign: str,
    term: Optional[str] = None,
    content: Optional[str] = None,
    **kwargs: Any,
) -> str:
    """Build a tracked URL with specified UTM parameters."""
    clean_base = sanitize_tracking_params(base_url, keep_utm=False)
    params = UTMParameters(
        base_url=clean_base,
        utm_source=source,
        utm_medium=medium,
        utm_campaign=campaign,
        utm_term=term,
        utm_content=content,
        custom_params={k: str(v) for k, v in kwargs.items()},
    )
    return params.build_url()


def build_platform_utm_url(
    base_url: str,
    platform: str,
    campaign: str,
    content: Optional[str] = None,
    term: Optional[str] = None,
) -> str:
    """Build a platform-customized UTM tracked URL using platform presets."""
    plat_key = platform.strip().lower()
    preset = PLATFORM_UTM_DEFAULTS.get(plat_key, {"source": plat_key, "medium": "social"})
    return build_utm_url(
        base_url=base_url,
        source=preset["source"],
        medium=preset["medium"],
        campaign=campaign,
        content=content,
        term=term,
    )


def generate_campaign_links(
    base_url: str,
    campaign: str,
    platforms: Optional[List[str]] = None,
    content: Optional[str] = None,
) -> Dict[str, str]:
    """Generate tracked URLs for multiple target platforms simultaneously."""
    target_platforms = platforms or ["twitter", "linkedin", "bluesky", "threads", "mastodon", "newsletter"]
    result: Dict[str, str] = {}
    for p in target_platforms:
        p_name = p.strip().lower()
        result[p_name] = build_platform_utm_url(
            base_url=base_url,
            platform=p_name,
            campaign=campaign,
            content=content,
        )
    return result


def tag_post_links(
    text: str,
    platform: str,
    campaign: str,
    content: Optional[str] = None,
) -> str:
    """Search for URLs within text and automatically replace them with platform UTM links."""
    def _replace(match: re.Match[str]) -> str:
        raw_url = match.group(0)
        trailing = ""
        while raw_url and raw_url[-1] in ".!?,;:)":
            trailing = raw_url[-1] + trailing
            raw_url = raw_url[:-1]
        return build_platform_utm_url(
            base_url=raw_url,
            platform=platform,
            campaign=campaign,
            content=content,
        ) + trailing

    return URL_REGEX.sub(_replace, text)


def generate_vanity_redirect_html(
    target_url: str,
    title: str,
    og_description: Optional[str] = None,
    og_image: Optional[str] = None,
    delay_ms: int = 0,
) -> str:
    """Generate a lightweight, zero-dependency static HTML redirect page.
    
    Includes Open Graph and Twitter card meta tags for link unfurling
    and meta refresh + JavaScript window.location.replace redirection.
    """
    safe_title = html.escape(title)
    safe_url = html.escape(target_url)
    delay_sec = max(0, int(delay_ms / 1000))

    og_desc_tag = f'<meta property="og:description" content="{html.escape(og_description)}">\n  <meta name="twitter:description" content="{html.escape(og_description)}">' if og_description else ""
    og_image_tag = f'<meta property="og:image" content="{html.escape(og_image)}">\n  <meta name="twitter:image" content="{html.escape(og_image)}">\n  <meta name="twitter:card" content="summary_large_image">' if og_image else '<meta name="twitter:card" content="summary">'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{safe_title}</title>
  <meta http-equiv="refresh" content="{delay_sec}; url={safe_url}">
  <meta property="og:title" content="{safe_title}">
  <meta property="og:url" content="{safe_url}">
  {og_desc_tag}
  {og_image_tag}
  <style>
    body {{
      font-family: system-ui, -apple-system, sans-serif;
      background: #0f172a;
      color: #f8fafc;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      margin: 0;
      text-align: center;
      padding: 24px;
    }}
    .box {{
      background: #1e293b;
      padding: 32px 48px;
      border-radius: 16px;
      box-shadow: 0 10px 25px rgba(0,0,0,0.5);
      max-width: 480px;
    }}
    h1 {{ font-size: 20px; margin-bottom: 12px; }}
    p {{ font-size: 14px; color: #94a3b8; line-height: 1.5; }}
    a.btn {{
      display: inline-block;
      margin-top: 16px;
      padding: 10px 20px;
      background: #3b82f6;
      color: #ffffff;
      text-decoration: none;
      border-radius: 8px;
      font-weight: 500;
    }}
  </style>
  <script>
    setTimeout(function() {{
      window.location.replace({json.dumps(target_url)});
    }}, {delay_ms});
  </script>
</head>
<body>
  <div class="box">
    <h1>{safe_title}</h1>
    <p>Redirecting to your destination...</p>
    <a class="btn" href="{safe_url}">Continue &rarr;</a>
  </div>
</body>
</html>"""
