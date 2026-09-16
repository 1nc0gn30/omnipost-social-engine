# 🤖 Model Context Protocol (MCP) Client Configurations

The **Omnipost Social Engine** exposes a full-featured [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server. This allows AI assistants like Anthropic Claude, Cursor, Cline, and Zed to directly analyze, optimize, split, and broadcast social media campaigns from within your editor or desktop app.

---

## 📁 Ready-to-Copy Configuration Files

| Client | Configuration File | Target Destination on Host |
|---|---|---|
| **Anthropic Claude Desktop** | [`claude_desktop_config.json`](./claude_desktop_config.json) | **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`<br>**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`<br>**Linux:** `~/.config/Claude/claude_desktop_config.json` |
| **Cursor IDE** | [`cursor_mcp.json`](./cursor_mcp.json) | `.cursor/mcp.json` (Workspace root) or Cursor Settings ➡️ MCP |
| **Cline (VS Code)** | [`cline_mcp.json`](./cline_mcp.json) | Cline Settings ➡️ MCP Servers tab or `cline_mcp_settings.json` |
| **Zed Editor** | [`zed_settings.json`](./zed_settings.json) | `~/.config/zed/settings.json` |

---

## 🛠️ Step-by-Step Setup

### 1. Claude Desktop Setup

1. Open Claude Desktop.
2. Go to **Settings** ➡️ **Developer** ➡️ **Edit Config**.
3. Merge the contents of [`claude_desktop_config.json`](./claude_desktop_config.json):

```json
{
  "mcpServers": {
    "omnipost-social-engine": {
      "command": "/path/to/venv/bin/python",
      "args": ["-m", "omnipost_social_engine.mcp_server"],
      "env": {
        "PYTHONPATH": "/path/to/omnipost-social-engine/src",
        "OMNIPOST_ENV": "production"
      }
    }
  }
}
```

4. Restart Claude Desktop. The 🔨 hammer icon will display available Omnipost tools.

---

### 2. Cursor IDE Setup

1. In your project workspace, create `.cursor/mcp.json`.
2. Paste the contents of [`cursor_mcp.json`](./cursor_mcp.json).
3. Open Cursor Settings ➡️ Features ➡️ MCP to verify `omnipost` status is green (Connected).

---

### 3. Cline (VS Code) Setup

1. Open the Cline sidebar in VS Code.
2. Click the **MCP Servers** icon in the header.
3. Click **Configure MCP Servers** and paste [`cline_mcp.json`](./cline_mcp.json).

---

### 4. Zed Editor Setup

1. Open `~/.config/zed/settings.json` in Zed.
2. Add the `context_servers` block from [`zed_settings.json`](./zed_settings.json).

---

## 🧰 Available MCP Tools

Once connected, your AI assistant will have access to the following native tools:

| Tool Name | Parameters | Description |
|---|---|---|
| `score_virality` | `content: str`, `platform: str` | Computes 0–100 virality index with actionable diagnostic breakdown. |
| `generate_thread` | `source_text: str`, `max_posts: int` | Splits essays or articles into numbered, character-bounded thread posts. |
| `convert_platform` | `content: str`, `target_platform: str` | Adapts post formatting, line breaks, and hashtags to target platform limits. |
| `optimize_hook` | `draft: str`, `framework: str` | Rewrites opening lines using viral psychological frameworks. |
| `validate_limits` | `content: str`, `platform: str` | Deterministically checks character length, media limits, and URL expansions. |
| `schedule_campaign` | `campaign_path: str` | Parses, validates, and stages a multi-post JSON campaign. |

---

## 💬 Sample Prompts to Give Your AI Assistant

- *"Claude, use `score_virality` on this tweet draft: 'We just released version 1.0 of our Python social engine. Check out the link on GitHub.'"*
- *"Cursor, take `docs/PLATFORM_LIMITS_GUIDE.md` and use `generate_thread` to produce a 6-part technical thread for Twitter and BlueSky."*
- *"Cline, load `examples/launch-campaign/campaign.json` and validate whether all posts satisfy each platform's character limits."*
