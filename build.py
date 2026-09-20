#!/usr/bin/env python3
"""Build index.html from the exported page bundle.

The design tool exports a self-contained bundle whose real document lives in a
JSON-encoded <script type="__bundler/template"> block. Its bootstrap ends with
documentElement.replaceWith(), which throws the wrapper's <head> away -- so a
<title> or favicon added to the wrapper never survives to the rendered page.
Anything we want in the served document has to go inside that template instead,
which is what this script does.

Run it after every re-export:  make build
"""

import base64
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
SOURCE = ROOT / "page.bundle.html"
OUTPUT = ROOT / "index.html"
FAVICON = ROOT / "img" / "favicon.png"

TITLE = "Hank Ehly"
DESCRIPTION = ("Data analytics consultant and software developer based in Japan. "
               "Interests include jokes, music, running, ML, AI, electronics and electricity.")
URL = "https://hankehly.com/"

TEMPLATE_RE = re.compile(
    r'(<script type="__bundler/template">)(.*?)(</script>)', re.DOTALL
)
# The bootstrap injects the template verbatim, so we hang our <head> additions
# off the one tag we know the export always emits.
ANCHOR = '<meta name="viewport" content="width=device-width, initial-scale=1">'


def head_additions():
    favicon = base64.b64encode(FAVICON.read_bytes()).decode("ascii")
    return "\n".join(
        [
            f"<title>{TITLE}</title>",
            f'<meta name="description" content="{DESCRIPTION}">',
            f'<meta property="og:type" content="website">',
            f'<meta property="og:url" content="{URL}">',
            f'<meta property="og:title" content="{TITLE}">',
            f'<meta property="og:description" content="{DESCRIPTION}">',
            f'<meta name="twitter:card" content="summary">',
            f'<link rel="icon" href="data:image/png;base64,{favicon}">',
        ]
    )


def encode_template(template):
    """JSON-encode the template for embedding back into a <script> block.

    json.dumps leaves "/" alone, so a literal </script> inside the string would
    close the tag early. Escaping it as <\\/ is valid JSON and parses back to
    the original text.
    """
    return json.dumps(template).replace("</", "<\\/")


def main():
    source = SOURCE.read_text(encoding="utf-8")

    match = TEMPLATE_RE.search(source)
    if not match:
        sys.exit(f"{SOURCE.name}: no __bundler/template block found")

    template = json.loads(match.group(2))

    if "<title>" in template:
        sys.exit(f"{SOURCE.name}: template already has a <title>; nothing to inject")
    if template.count(ANCHOR) != 1:
        sys.exit(
            f"{SOURCE.name}: expected exactly one viewport meta in the template, "
            f"found {template.count(ANCHOR)}"
        )

    template = template.replace(ANCHOR, ANCHOR + "\n" + head_additions(), 1)

    built = (
        source[: match.start()]
        + match.group(1)
        + encode_template(template)
        + match.group(3)
        + source[match.end() :]
    )
    # The wrapper's own title is discarded at runtime, but it is what a crawler
    # or a "view source" sees before any JavaScript runs.
    built = built.replace("<title>Bundled Page</title>", f"<title>{TITLE}</title>", 1)

    OUTPUT.write_text(built, encoding="utf-8")
    print(f"wrote {OUTPUT.name} ({len(built):,} bytes)")


if __name__ == "__main__":
    main()
