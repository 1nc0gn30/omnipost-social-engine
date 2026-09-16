# 📊 Social Media Platform Limits & Technical Specifications Guide

A comprehensive, deterministic engineering reference for character limits, media specifications, rate limits, and formatting rules across major social platforms.

---

## 📋 Platform Limits Master Comparison

| Platform | Max Character Limit | Truncation / "See More" Cutoff | Max Images | Max Image Size | Max Video Length | Native Markdown Support |
|---|---|---|---|---|---|---|
| **𝕏 / Twitter** | **280** (Standard)<br>*25,000 (Premium)* | 280 chars | 4 | 5 MB | 140s (Standard)<br>*2–3 hrs (Premium)* | ❌ (Plain text / Unicode) |
| **💼 LinkedIn** | **3,000** (Post)<br>*120,000 (Article)* | ~210 characters | 9 | 8 MB | 10 minutes | ❌ (Plain text / Unicode) |
| **🦋 BlueSky (ATProto)**| **300** (Graphemes) | 300 chars | 4 | 1 MB | 60 seconds | ❌ (ATProto Facets) |
| **🧵 Threads** | **500** | 500 chars | 10 | 8 MB | 5 minutes | ❌ (Plain text) |
| **🐘 Mastodon (Fediverse)**| **500** (Default)<br>*(Configurable per instance)* | 500 chars | 4 | 8 MB | 40 MB (~3 mins) | ⚠️ (HTML / Plain text) |

---

## 🔍 Character Counting Algorithms by Platform

### 1. Twitter / X Weighted Character Rules
Twitter does NOT count standard character length linearly:
* **Standard Latin Characters (ASCII):** 1 character point.
* **Emojis & Multi-byte Glyphs:** 2 character points.
* **URLs:** Any valid URL (`http://` or `https://`) is automatically mapped to `t.co` and consumes exactly **23 characters**, regardless of actual length.
* **Mentions (`@username`):** In direct replies, leading mentions do not count against the 280-character budget.

```python
import re

def twitter_char_count(text: str) -> int:
    # Replace URLs with 23 placeholder characters
    url_pattern = r'https?://\S+'
    text_without_urls = re.sub(url_pattern, 'X' * 23, text)
    
    count = 0
    for char in text_without_urls:
        # CJK / Emojis / Astral Plane count as 2
        if ord(char) > 0x1000 or (0x2000 <= ord(char) <= 0x3300):
            count += 2
        else:
            count += 1
    return count
```

---

### 2. BlueSky (ATProto) Facet Byte Encoding
BlueSky counts characters in **Unicode Grapheme Clusters** (max 300), but links and mentions are embedded as **Rich Text Facets** defined by UTF-8 byte offsets `[byteStart, byteEnd]`:

```json
{
  "$type": "app.bsky.richtext.facet",
  "index": {
    "byteStart": 14,
    "byteEnd": 35
  },
  "features": [
    {
      "$type": "app.bsky.richtext.facet#link",
      "uri": "https://github.com/omnipost"
    }
  ]
}
```

> ⚠️ **Warning:** Byte offsets must be calculated on the raw UTF-8 encoded byte array (`text.encode('utf-8')`), NOT string indices.

---

### 3. LinkedIn Truncation Mechanics
While LinkedIn allows up to 3,000 characters:
* On desktop, the feed truncates at **~210 characters** before displaying `...see more`.
* On mobile, truncation happens at **3 lines of text**.
* **Engine Rule:** Place the core curiosity hook and key question within the first 180 characters.

---

## 🖼️ Media Dimension & Aspect Ratio Matrix

```
┌─────────────────┬──────────────────────┬──────────────────────┬──────────────────────┐
│ Platform        │ Recommended Aspect   │ Ideal Dimensions     │ Supported Formats    │
├─────────────────┼──────────────────────┼──────────────────────┼──────────────────────┤
│ Twitter / X     │ 16:9 (Landscape)     │ 1200 x 675 px        │ JPEG, PNG, WEBP, GIF │
│                 │ 1:1 (Square)         │ 1080 x 1080 px       │                      │
├─────────────────┼──────────────────────┼──────────────────────┼──────────────────────┤
│ LinkedIn        │ 4:5 (Vertical)       │ 1080 x 1350 px       │ JPEG, PNG, PDF Docs  │
│                 │ 1.91:1 (Link Card)   │ 1200 x 627 px        │                      │
├─────────────────┼──────────────────────┼──────────────────────┼──────────────────────┤
│ BlueSky         │ 16:9 / 1:1           │ 1200 x 675 px        │ JPEG, PNG, WEBP      │
├─────────────────┼──────────────────────┼──────────────────────┼──────────────────────┤
│ Threads         │ 9:16 (Vertical)      │ 1080 x 1920 px       │ JPEG, PNG, QuickTime │
│                 │ 1:1 (Square)         │ 1080 x 1080 px       │                      │
├─────────────────┼──────────────────────┼──────────────────────┼──────────────────────┤
│ Mastodon        │ 16:9 / 1:1           │ 1200 x 675 px        │ JPEG, PNG, GIF, MP4  │
└─────────────────┴──────────────────────┴──────────────────────┴──────────────────────┘
```

---

## ⏱️ API Rate Limits & Leaky Bucket Strategies

To prevent `HTTP 429 Too Many Requests` when broadcasting multi-post campaigns, Omnipost enforces per-platform Leaky Bucket limits:

```
Platform        Burst Limit (Req/Min)   Sustained Limit (Req/Day)   Recommended Backoff
────────────────────────────────────────────────────────────────────────────────────────
Twitter v2      50 tweets / 15 mins     1,500 / month (Free tier)   Exponential (2^n + jitter)
LinkedIn API    100 shares / day        1,000 / day (Org level)     Fixed 2.0s sleep
BlueSky API     5,000 req / 5 mins      100,000 / day               Token bucket
Mastodon        300 requests / 5 mins   Instance specific           Retry-After header respect
Threads API     250 posts / 24 hrs      1,000 / day                 Sliding window
```

---

## 🔤 Unicode Typography Translation Map

Since social platforms do not support native Markdown bold or italics in feed posts, Omnipost translates standard characters to Mathematical Alphanumeric Unicode code points:

* **Sans-Serif Bold:** `A` (`0x41`) ➡️ `𝗔` (`0x1D5D4`), `a` (`0x61`) ➡️ `𝗮` (`0x1D5EE`)
* **Sans-Serif Italic:** `A` (`0x41`) ➡️ `𝘈` (`0x1D608`), `a` (`0x61`) ➡️ `𝘢` (`0x1D622`)
* **Monospace:** `A` (`0x41`) ➡️ `𝙰` (`0x1D670`), `a` (`0x61`) ➡️ `𝚊` (`0x1D68A`)
* **Strikethrough:** Combines character with combining long stroke overlay (`\u0336`).

> ℹ️ *All Unicode code points are fully accessible and render consistently on iOS, Android, macOS, Linux, and Windows.*
