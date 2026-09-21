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
COUNTER = "https://abacus.jasoncameron.dev/hit/hankehly.com/visits"

# The export seeds the visitor counter from localStorage, which makes it a
# per-browser number dressed up as a site-wide one. We swap that back out for
# the shared Abacus counter here rather than in the bundle, because the bundle
# is overwritten by the next re-export.
COUNTER_PATCHES = [
    # Drop the localStorage seed; `visits` becomes state fetched at mount.
    (
        """    let booted = false, visits = 1;
    try { booted = sessionStorage.getItem('hank95_booted') === '1'; } catch(e){}
    try {
      visits = Number(localStorage.getItem('hank95_visits') || 0) + 1;
      localStorage.setItem('hank95_visits', String(visits));
    } catch(e){}""",
        """    let booted = false;
    try { booted = sessionStorage.getItem('hank95_booted') === '1'; } catch(e){}""",
    ),
    # Start empty so the display shows a placeholder until the fetch lands.
    (
        "      tip: null, visits: visits + 1046,",
        "      tip: null, visits: null,",
    ),
    # Register the hit once, right after the clock timer is installed.
    (
        "    }, 1000);\n",
        "    }, 1000);\n"
        f"    fetch('{COUNTER}')\n"
        "      .then(r => r.json()).then(d => this.setState({ visits: d.value })).catch(() => {});\n",
    ),
    # The export assumed a number; restore the guard so a failed or in-flight
    # request renders '------' instead of 'null'.
    (
        "      visits: String(st.visits).padStart(6, '0'),",
        "      visits: st.visits == null ? '------' : String(st.visits).padStart(6, '0'),",
    ),
]

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


def restore_hit_counter(template):
    """Swap the export's per-browser visit count for the shared Abacus counter.

    If a future export already fetches the counter itself, there is nothing to
    do -- that is the fix landing upstream, not a failure.
    """
    if COUNTER in template:
        print("hit counter: already in the export, left alone")
        return template

    for old, new in COUNTER_PATCHES:
        found = template.count(old)
        if found != 1:
            sys.exit(
                f"{SOURCE.name}: hit-counter patch expected exactly one match for "
                f"{old.splitlines()[0].strip()!r}, found {found}"
            )
        template = template.replace(old, new, 1)

    print("hit counter: restored the Abacus counter")
    return template


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
    template = restore_hit_counter(template)

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
