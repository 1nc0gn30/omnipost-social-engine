# 🚀 Omnipost Product Launch Campaign Example

This directory contains a complete, production-ready **Omnichannel Product Launch Campaign** designed for software engineers, developer advocates, and indie hackers launching developer tools or open-source software.

---

## 📂 Files in this Directory

| File | Purpose |
|------|---------|
| [`campaign.json`](./campaign.json) | Complete structured JSON campaign specification containing post variants, scheduled timestamps, media attachments, virality targets, and UTM parameters across 5 platforms. |
| [`posts.csv`](./posts.csv) | Standardized CSV export ready for programmatic ingestion, spreadsheet review, or third-party scheduler upload. |

---

## 🎯 Campaign Strategy & Lifecycle

This launch campaign follows a proven 4-stage social media playbook:

```
[Phase 1: Teaser]  --->  [Phase 2: Main Launch]  --->  [Phase 3: Deep Dive]  --->  [Phase 4: Community AMA]
 24 Hours Prior            Launch Day (Peak)            Day 2 (Tech Specs)          Day 3 (Engagement)
```

1. **Phase 1: The Teaser (`post-001`)**
   - **Goal:** Build anticipation and trigger notification bell clicks without prematurely revealing all technical details.
   - **Timing:** 24 hours prior to release (13:00 UTC).
2. **Phase 2: The Main Announcement (`post-002`)**
   - **Goal:** Maximum virality, repository stars, and link clicks.
   - **Timing:** Launch Day at 14:00 UTC (peak overlap between US East & European engineering timezones).
   - **Features:** Mathematical Unicode bold typography (`🚀 𝗪𝗲 𝗷𝘂𝘀𝘁 𝗼𝗽𝗲𝗻-𝘀𝗼𝘂𝗿𝗰𝗲𝗱...`), high-res 1200x630 banner asset, explicit CTA.
3. **Phase 3: The Technical Deep-Dive (`post-003`)**
   - **Goal:** Earn credibility with senior engineers and architecture enthusiasts.
   - **Timing:** Day 2 at 15:30 UTC.
   - **Features:** Thread format detailing internal AST parsing, Unicode code points, and Model Context Protocol (MCP) tool design.
4. **Phase 4: Community AMA & Feedback Loop (`post-004`)**
   - **Goal:** High reply volume and algorithmic re-amplification through audience polling.
   - **Timing:** Day 3 at 17:00 UTC.

---

## 🛠️ How to Use This Campaign

### 1. Dry Run / Validate via CLI

Validate character limits, media attachments, and platform envelope rules locally:

```bash
# Validate the campaign configuration
python -m omnipost_social_engine.cli validate examples/launch-campaign/campaign.json

# Output:
# ✅ Campaign 'omnipost-v1-launch' validated successfully.
# ✅ 4 posts across 5 platforms checked. 0 character overflow errors.
```

### 2. Simulate in Google Omnipost Studio

Open the local Material 3 Studio:

```bash
# Open public/index.html in your browser
open public/index.html
```

- Navigate to the **Multi-Platform Composer & Simulator** tab.
- Paste any post from `campaign.json` or `posts.csv` into the editor to preview exact mobile/desktop renderings for Twitter, LinkedIn, BlueSky, Threads, and Mastodon.

### 3. Programmatic Execution with Python

```python
import json
from pathlib import Path

# Load campaign definition
campaign_path = Path("examples/launch-campaign/campaign.json")
with open(campaign_path, "r", encoding="utf-8") as f:
    campaign_data = json.load(f)

print(f"Loaded campaign: {campaign_data['title']}")
for post in campaign_data["posts"]:
    print(f"[{post['scheduled_time']}] Stage: {post['stage']} | Platforms: {', '.join(post['platforms'])}")
```

### 4. Execute via Model Context Protocol (MCP)

If running within Claude Desktop or Cursor:

> *"Claude, load the campaign in `examples/launch-campaign/campaign.json` and verify if the character counts on post-002 satisfy BlueSky's 300-character limit."*

---

## 🏷️ UTM Tracking Discipline

The campaign automatically generates clean UTM parameters using the `{platform}` and `{stage}` dynamic template tags:

```
https://github.com/omnipost/omnipost-social-engine?utm_source=twitter&utm_medium=social&utm_campaign=omnipost_launch_v1&utm_content=main_launch
```
