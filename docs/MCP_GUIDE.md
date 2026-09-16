# 🤖 Model Context Protocol (MCP) Server Guide

The **Omnipost Social Engine** provides a native, zero-dependency [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server. This enables Large Language Models (LLMs) and autonomous AI coding assistants (such as Anthropic Claude Desktop, Cursor, Cline, and Zed) to directly interact with Omnipost tools.

---

## 🏛️ Architecture Overview

The Omnipost MCP server implements the JSON-RPC 2.0 specification over standard input/output (`stdio`) or Server-Sent Events (`SSE`):

```
┌─────────────────────────────────────────────────────────────┐
│                 LLM Host / AI Client                        │
│   (Claude Desktop / Cursor IDE / Cline / Zed / Custom Agent)│
└──────────────────────────────┬──────────────────────────────┘
                               │ JSON-RPC 2.0 over stdio
                               ▼
┌─────────────────────────────────────────────────────────────┐
│              Omnipost MCP Server Dispatcher                 │
│         (omnipost_social_engine.mcp_server)                 │
├─────────────────────────────────────────────────────────────┤
│  Tools:                                                     │
│   • score_virality()       • generate_thread()              │
│   • convert_platform()     • optimize_hook()                │
│   • validate_limits()      • schedule_campaign()            │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 Omnipost Core Engine                        │
│  (AST Tokenizer, Platform Envelopes, Leaky Bucket Limiter)  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧰 Exposed MCP Tools & Schemas

### 1. `score_virality`
Evaluates social media draft copy and returns an algorithmic 0–100 virality score with a breakdown of hook power, readability, CTA strength, spacing, and hashtag density.

* **Schema:**
```json
{
  "name": "score_virality",
  "description": "Calculate algorithmic virality score (0-100) and diagnostic recommendations for social copy.",
  "parameters": {
    "type": "object",
    "properties": {
      "content": {
        "type": "string",
        "description": "The raw post text to analyze."
      },
      "platform": {
        "type": "string",
        "enum": ["twitter", "linkedin", "bluesky", "threads", "mastodon"],
        "default": "twitter"
      }
    },
    "required": ["content"]
  }
}
```

* **Sample Response:**
```json
{
  "virality_score": 94,
  "grade": "Viral Contender",
  "breakdown": {
    "hook_power": 28,
    "readability": 19,
    "cta_strength": 18,
    "line_spacing": 15,
    "hashtag_hygiene": 14
  },
  "recommendations": [
    "Hook question captures attention in the first 70 characters.",
    "Optimal paragraph spacing detected."
  ]
}
```

---

### 2. `generate_thread`
Splits long articles, markdown files, or essays into structured, character-bounded social thread cards.

* **Schema:**
```json
{
  "name": "generate_thread",
  "description": "Split long-form text into numbered thread posts adhering to platform character limits.",
  "parameters": {
    "type": "object",
    "properties": {
      "source_text": {
        "type": "string",
        "description": "The markdown or text to split into thread cards."
      },
      "max_posts": {
        "type": "integer",
        "default": 10
      },
      "numbering_style": {
        "type": "string",
        "enum": ["fraction", "slash", "bracket", "dot", "thread", "none"],
        "default": "fraction"
      },
      "max_chars_per_post": {
        "type": "integer",
        "default": 280
      }
    },
    "required": ["source_text"]
  }
}
```

---

### 3. `convert_platform`
Adapts a post written for one platform to the character limits, markdown support, and formatting conventions of another platform.

* **Schema:**
```json
{
  "name": "convert_platform",
  "description": "Adapt post formatting, hashtags, and envelopes from source to target platform.",
  "parameters": {
    "type": "object",
    "properties": {
      "content": {
        "type": "string"
      },
      "source_platform": {
        "type": "string",
        "enum": ["twitter", "linkedin", "bluesky", "threads", "mastodon"],
        "default": "twitter"
      },
      "target_platform": {
        "type": "string",
        "enum": ["twitter", "linkedin", "bluesky", "threads", "mastodon"]
      }
    },
    "required": ["content", "target_platform"]
  }
}
```

---

### 4. `optimize_hook`
Rewrites draft opening lines into high-converting hook variants using proven psychological copywriting frameworks.

* **Schema:**
```json
{
  "name": "optimize_hook",
  "description": "Generate high-converting hook variations based on psychological formulas.",
  "parameters": {
    "type": "object",
    "properties": {
      "draft": {
        "type": "string",
        "description": "The initial idea or draft sentence."
      },
      "framework": {
        "type": "string",
        "enum": ["curiosity_gap", "contrarian", "playbook", "data_breakdown", "story_turnaround", "mistakes"],
        "default": "curiosity_gap"
      }
    },
    "required": ["draft"]
  }
}
```

---

### 5. `validate_limits`
Performs deterministic limit checks against platform specs (character count, t.co URL expansion, ATProto facets, image attachments, video durations).

* **Schema:**
```json
{
  "name": "validate_limits",
  "description": "Validate post content and media against specific platform technical limits.",
  "parameters": {
    "type": "object",
    "properties": {
      "content": { "type": "string" },
      "platform": { "type": "string", "enum": ["twitter", "linkedin", "bluesky", "threads", "mastodon"] },
      "media_count": { "type": "integer", "default": 0 }
    },
    "required": ["content", "platform"]
  }
}
```

---

### 6. `schedule_campaign`
Parses and validates a full campaign JSON file (e.g., `examples/launch-campaign/campaign.json`).

* **Schema:**
```json
{
  "name": "schedule_campaign",
  "description": "Stage or validate a multi-post campaign definition file.",
  "parameters": {
    "type": "object",
    "properties": {
      "campaign_path": { "type": "string" },
      "dry_run": { "type": "boolean", "default": true }
    },
    "required": ["campaign_path"]
  }
}
```

---

## ⚙️ Client Configuration Reference

### Claude Desktop
File: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "omnipost-social-engine": {
      "command": "python3",
      "args": ["-m", "omnipost_social_engine.mcp_server"],
      "env": {
        "PYTHONPATH": "/path/to/omnipost-social-engine/src"
      }
    }
  }
}
```

### Cursor IDE
File: `.cursor/mcp.json`

```json
{
  "mcpServers": {
    "omnipost": {
      "command": "python",
      "args": ["-m", "omnipost_social_engine.mcp_server"],
      "env": {
        "PYTHONPATH": "src"
      }
    }
  }
}
```

---

## 🔍 Debugging MCP Server Locally

Test the MCP server directly from the command line using standard JSON-RPC 2.0 payloads:

```bash
# Start server in stdio mode
PYTHONPATH=src python -m omnipost_social_engine.mcp_server
```

Send a `tools/list` request via stdin:

```json
{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
```

Test a tool execution (`score_virality`):

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "score_virality",
    "arguments": {
      "content": "🚀 We just open-sourced Omnipost Social Engine! Check it out: https://github.com/omnipost/omnipost-social-engine",
      "platform": "twitter"
    }
  }
}
```
