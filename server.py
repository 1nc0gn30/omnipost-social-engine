#!/usr/bin/env python3
"""OmniPost Social Engine Standalone Production Server on Port 8091.

Provides real REST API endpoints:
  - /health & /api/health
  - /api/mcp/config
  - /api/diagnostics
  - /api/hooks
  - /api/format
  - /api/split
  - /api/analyze
  - /api/export
  - /api/export-bundle
and serves the standalone OmniPost Studio from public/.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
PUBLIC_DIR = ROOT_DIR / "public"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from omnipost_social_engine.ui_server import run_server

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="OmniPost Social Engine Standalone Workstation")
    parser.add_argument("--port", type=int, default=8091, help="Port to listen on (default: 8091)")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface (default: 127.0.0.1)")
    args = parser.parse_args()

    print(f"Starting OmniPost Social Engine Server on {args.host}:{args.port}...")
    run_server(host=args.host, port=args.port)
