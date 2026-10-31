#!/usr/bin/env python3
"""Move embedded (base64 data URI) fonts out of a captured page into shared files.

  python3 extract_assets.py RUN_DIR/site/v0/index.html

capture.js embeds web fonts as data URIs so the snapshot is one self-contained download.
That makes the HTML huge (often 0.5–1 MB), and the design agent reads it every round.
This writes each font once to RUN_DIR/site/assets/fonts/<hash>.<ext> and rewrites the
url(...) to a relative path, so every version (site/vN/) can share them via
`../assets/fonts/...`. Prints the size before and after. Standard library only.
"""
import base64
import hashlib
import os
import re
import sys
from pathlib import Path

EXT = {"woff2": "woff2", "woff": "woff", "ttf": "ttf", "truetype": "ttf", "otf": "otf",
       "opentype": "otf", "sfnt": "ttf", "vnd.ms-fontobject": "eot"}
DATA_URI = re.compile(r"data:(?:font|application)/(?:x-)?(?:font-)?([\w.+-]+);base64,([A-Za-z0-9+/=]+)")


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    html_path = Path(sys.argv[1]).resolve()
    site = html_path.parent.parent                      # RUN_DIR/site
    fonts = site / "assets" / "fonts"
    fonts.mkdir(parents=True, exist_ok=True)
    rel = os.path.relpath(fonts, html_path.parent).replace(os.sep, "/")

    text = html_path.read_text(encoding="utf-8")
    before = len(text.encode("utf-8"))
    count = 0

    def swap(m):
        nonlocal count
        kind, payload = m.group(1).lower(), m.group(2)
        try:
            data = base64.b64decode(payload, validate=True)
        except ValueError:
            return m.group(0)
        name = f"{hashlib.sha1(data).hexdigest()[:16]}.{EXT.get(kind, 'woff2')}"
        target = fonts / name
        if not target.exists():
            target.write_bytes(data)
        count += 1
        return f"{rel}/{name}"

    text = DATA_URI.sub(swap, text)
    html_path.write_text(text, encoding="utf-8")
    after = len(text.encode("utf-8"))
    print(f"{count} embedded font(s) moved to {fonts}; {before // 1024} KB -> {after // 1024} KB")


if __name__ == "__main__":
    main()
