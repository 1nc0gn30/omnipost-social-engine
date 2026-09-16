# 📚 Omnipost Social Engine — Production Examples Catalog

Welcome to the examples directory for **Omnipost Social Engine**. This repository provides production-tested configurations, datasets, threads, and AI agent integration templates.

---

## 📂 Directory Index

| Example | Path | Description |
|---|---|---|
| 🚀 **Product Launch Campaign** | [`examples/launch-campaign/`](./launch-campaign/) | Full 4-phase omnichannel product launch dataset (`campaign.json`, `posts.csv`) with UTM tracking, media assets, and platform envelopes across X, LinkedIn, BlueSky, Threads, and Mastodon. |
| 🧵 **Developer Technical Thread** | [`examples/developer-thread/`](./developer-thread/) | High-converting 10-part technical developer thread (`thread.md`) breaking down Python async architecture, Unicode typography, and MCP server design with character limits < 280. |
| 🤖 **MCP Client Integrations** | [`examples/mcp-clients/`](./mcp-clients/) | Ready-to-copy JSON configuration files for Anthropic Claude Desktop, Cursor IDE, Cline, and Zed editor. |

---

## ⚡ Quickstart Commands

### 1. Test the Launch Campaign JSON

```bash
# Verify campaign JSON validity
python -c "
import json
with open('examples/launch-campaign/campaign.json') as f:
    data = json.load(f)
print('Loaded campaign:', data['title'], 'with', len(data['posts']), 'posts')
"
```

### 2. Parse & Verify Developer Thread

```bash
# Verify character counts for all 10 posts
python -c "
from pathlib import Path
content = Path('examples/developer-thread/thread.md').read_text()
posts = [p.strip() for p in content.split('---') if 'Post ' in p]
print(f'Total thread posts: {len(posts)}')
for i, p in enumerate(posts, 1):
    print(f'Post {i}: {len(p)} characters')
"
```

### 3. Launch the Google Omnipost Web Studio

```bash
# Open the standalone Material 3 Studio in your default browser
open public/index.html
# or on Linux:
xdg-open public/index.html
```

---

## 🛠️ Contributing New Examples

Have a high-performing campaign template, developer thread, or novel MCP workflow?
Contributions are welcome! Please submit a PR following the directory conventions outlined in [`CONTRIBUTING.md`](../README.md#contributing).
