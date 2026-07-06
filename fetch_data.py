#!/usr/bin/env python3
"""
Canonical regional fetch entrypoint.

Delegates to the robust paged downloader with retries and fallbacks.
Included so fresh stages land in input/ for:
  python3 scripts/diversify_formats.py
"""

import runpy
from pathlib import Path

path = Path(__file__).resolve().parent / "scripts" / "fetch_data_robust.py"
runpy.run_path(str(path), run_name="__main__")
