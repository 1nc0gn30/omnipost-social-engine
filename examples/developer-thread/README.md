# 🧵 Developer Technical Thread Example

This directory contains an example of a **10-part viral technical thread** formatted for multi-platform broadcasting across Twitter/X, BlueSky, Threads, and LinkedIn.

---

## 📂 Files

- [`thread.md`](./thread.md): The raw 10-part technical thread markdown file.

---

## 📐 Thread Specifications & Quality Checks

Each post in `thread.md` adheres to strict developer advocacy standards:

1. **Character Constraints**: Every post is strictly under **280 characters** (including numbering prefixes, code fences, and URLs).
2. **Hook Integrity**: Post 1 utilizes the *Problem + Curiosity Gap* framework to hook scrolling developers.
3. **Structured Flow**:
   - Posts 1–3: Core Problem & Universal Representation.
   - Posts 4–6: Internal Algorithms (Unicode Math, Thread Splitting, Virality Scoring).
   - Posts 7–9: Systems Architecture (Async Leaky Bucket, MCP Server, M3 Web Studio).
   - Post 10: Clear Call-To-Action (GitHub Star + Repost CTA).
4. **Code Precision**: Code blocks are trimmed to essential syntax to maximize mobile readability.

---

## 🚀 How to Ingest and Broadcast

### Using the Python API

```python
from pathlib import Path

def parse_thread(md_file: Path) -> list[str]:
    raw = md_file.read_text(encoding="utf-8")
    sections = raw.split("\n---\n")
    posts = []
    for sec in sections:
        lines = [line for line in sec.strip().split("\n") if not line.startswith("#")]
        content = "\n".join(lines).strip()
        if content:
            posts.append(content)
    return posts

thread_posts = parse_thread(Path("examples/developer-thread/thread.md"))
print(f"Extracted {len(thread_posts)} thread posts.")
for i, post in enumerate(thread_posts, 1):
    print(f"Post #{i} ({len(post)} chars): {post[:40]}...")
```

### Using Google Omnipost Studio

1. Open `public/index.html`.
2. Select the **🧵 Smart Thread Splitter** tab.
3. Choose `Custom Delimiter (---)` mode.
4. Paste the content of `thread.md`.
5. Preview, re-order, edit, and export to JSON or clipboard in one click!
