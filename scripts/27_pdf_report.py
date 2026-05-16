"""Render the densest-circle writeup as a styled HTML page and convert to PDF
via headless Chrome.

Output: reports/densest_circle_full_writeup.pdf
"""

from __future__ import annotations

import base64
import re
import subprocess
import sys
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
MD_FILE = REPORTS / "densest_circle_full_writeup.md"
HTML_FILE = REPORTS / "_densest_circle_full_writeup.html"
PDF_FILE = REPORTS / "densest_circle_full_writeup.pdf"

REPO_URL = "https://github.com/jameshartt/BHPLTA-densest-circle-report"
REPO_BRANCH = "main"
REPO_BLOB = f"{REPO_URL}/blob/{REPO_BRANCH}"
REPO_TREE = f"{REPO_URL}/tree/{REPO_BRANCH}"
REPO_RAW = f"{REPO_URL}/raw/{REPO_BRANCH}"
PDF_HREF = "./densest_circle_full_writeup.pdf"
OSM_WIKI = "https://wiki.openstreetmap.org/wiki"


CSS = """
@page {
  size: A4;
  margin: 18mm 16mm 18mm 16mm;
  @bottom-right { content: counter(page) " / " counter(pages); }
}
* { box-sizing: border-box; }
html, body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  font-size: 11pt;
  color: #1f2933;
  line-height: 1.45;
  margin: 0; padding: 0;
}
/* Screen-only styling — when viewed in a browser, give the content a
   readable column width and breathing room around the edges. Print
   media (PDF rendering) keeps the existing @page margins and ignores
   these screen rules. */
@media screen {
  body {
    max-width: 780px;
    margin: 0 auto;
    padding: 32px 24px 64px;
    background: #fafafa;
  }
}
@media screen and (max-width: 640px) {
  body { padding: 16px 14px 32px; font-size: 14px; }
}
h1 {
  font-size: 22pt;
  color: #9d0f33;
  margin: 0 0 8pt 0;
  page-break-after: avoid;
}
h2 {
  font-size: 16pt;
  color: #1f2933;
  border-bottom: 2px solid #e3174a;
  padding-bottom: 4pt;
  margin-top: 18pt;
  page-break-after: avoid;
  page-break-before: always;
}
/* …but no page break before the very first H2 of the document
   (otherwise the title page contains only the H1 + a blank). */
h1 + h2,
h2:first-of-type {
  page-break-before: auto;
}
h3 {
  font-size: 13pt;
  color: #1f2933;
  margin-top: 14pt;
  page-break-after: avoid;
}
p { margin: 6pt 0; }
em { color: #5a5a5a; }
strong { color: #1f2933; }
hr {
  border: 0;
  border-top: 1px solid #d0d0d0;
  margin: 14pt 0;
}
blockquote {
  border-left: 4px solid #e3174a;
  background: #fdf0f3;
  margin: 10pt 0;
  padding: 8pt 14pt;
  color: #1f2933;
  font-style: normal;
}
blockquote strong { color: #9d0f33; }
table {
  border-collapse: collapse;
  margin: 8pt 0;
  font-size: 10pt;
  page-break-inside: avoid;
  width: 100%;
}
th, td {
  border-bottom: 1px solid #dcdcdc;
  padding: 4pt 8pt;
  text-align: left;
  vertical-align: top;
}
th {
  background: #f4f5f7;
  font-weight: 600;
  border-bottom: 2px solid #b0b8c0;
}
tr:nth-child(even) td { background: #fafbfc; }
code, pre {
  font-family: "Menlo", "Monaco", "Consolas", monospace;
  font-size: 9.5pt;
  background: #f4f5f7;
  border-radius: 3px;
  padding: 1px 4px;
}
pre { padding: 8pt; overflow-x: auto; }
ul, ol { margin: 6pt 0 6pt 18pt; }
li { margin: 2pt 0; }
img {
  max-width: 100%;
  height: auto;
  display: block;
  margin: 10pt auto;
  page-break-inside: avoid;
}
a { color: #9d0f33; text-decoration: none; }
a:hover { text-decoration: underline; }
.cover {
  text-align: center;
  padding-top: 20mm;
}
.cover h1 { font-size: 28pt; margin-bottom: 6pt; }
.cover .subtitle { font-size: 13pt; color: #555; font-style: italic; }
.cover .footer { margin-top: 30mm; font-size: 10pt; color: #888; }

/* Repo banner — shown on screen only, hidden in PDF. */
.repo-banner {
  background: #1f2933;
  color: #f4f5f7;
  padding: 10px 16px;
  margin-bottom: 24px;
  border-radius: 4px;
  font-size: 11pt;
  display: flex;
  flex-wrap: wrap;
  gap: 6px 14px;
  align-items: center;
  justify-content: center;
}
.repo-banner a {
  color: #ffb4c8;
  text-decoration: underline;
  font-weight: 600;
}
.repo-banner a:hover { color: #ffd9e2; }
.repo-banner .sep { color: #6a7480; }
.repo-banner .gh-icon {
  display: inline-block;
  vertical-align: -3px;
  margin-right: 4px;
}
.repo-footer {
  margin-top: 22pt;
  padding-top: 14pt;
  border-top: 1px solid #d0d0d0;
  font-size: 10pt;
  color: #5a5a5a;
}
.repo-footer a { color: #9d0f33; }
img.linked-asset { cursor: zoom-in; }
@media print {
  .repo-banner, .repo-footer { display: none; }
}
"""


def md_to_html(md_text: str) -> str:
    body_html = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "toc"],
    )
    return body_html


def embed_image(match: re.Match) -> str:
    """Convert markdown image references to inline base64 (for PDF self-containment),
    wrapped in an <a> linking to the source PNG on GitHub so screen readers can
    click through to the full-resolution copy."""
    alt = match.group(1)
    path_str = match.group(2)
    p = (REPORTS / path_str).resolve()
    if not p.exists():
        return f'<em>(missing image: {path_str})</em>'
    data = p.read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    suffix = p.suffix.lstrip(".").lower()
    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "svg": "image/svg+xml"}.get(suffix, "image/png")
    # Reconstruct the repo-relative path (markdown uses ./foo.png; resolve against reports/).
    try:
        rel = p.relative_to(ROOT).as_posix()
    except ValueError:
        rel = f"reports/{p.name}"
    href = f"{REPO_BLOB}/{rel}"
    return (
        f'<a href="{href}" target="_blank" rel="noopener" '
        f'title="Open full-resolution {p.name} on GitHub">'
        f'<img class="linked-asset" alt="{alt}" src="data:{mime};base64,{b64}">'
        f'</a>'
    )


# --------------------------------------------------------------------------
# Asset-link post-processing
# --------------------------------------------------------------------------

_SCRIPT_RE = re.compile(r"^(?:scripts/)?(\d{2}_[a-z0-9_]+\.py)$")
_GROUND_TRUTH_FILE_RE = re.compile(r"^reports/ground_truth/([a-z_]+)\.md$")
_OSM_TAG_RE = re.compile(r"^([a-z_]+)=([a-z_0-9]+)$")
_OSM_COMPOUND_TAG_RE = re.compile(r"^[a-z_]+=[a-z_0-9]+(?:\s*[+,]\s*[a-z_]+=[a-z_0-9]+)+$")
_OSM_TAG_TOKEN_RE = re.compile(r"\b([a-z_]+)=([a-z_0-9]+)\b")
_PRE_GROUND_TRUTH_LINE_RE = re.compile(r"^(reports/ground_truth/[a-z_]+\.md)$")

# Bare leisure-value tokens that appear in this writeup as shorthand for
# `leisure=<value>` — linked to the OSM wiki page for that tag.
_BARE_LEISURE_VALUES = {
    "recreation_ground",
    "garden",
    "common",
    "nature_reserve",
}

_DIRECTORY_LINKS = {
    "scripts/": f"{REPO_TREE}/scripts",
    "data/processed/": f"{REPO_TREE}/data/processed",
    "data/raw/": f"{REPO_TREE}/data/raw",
    "reports/": f"{REPO_TREE}/reports",
    "reports/ground_truth/*.md": f"{REPO_TREE}/reports/ground_truth",
    "reports/ground_truth/": f"{REPO_TREE}/reports/ground_truth",
    "~/Development/Tennis/tennis-courts-analysis": REPO_URL,
}


def _wrap_code(text: str, href: str, title: str | None = None) -> str:
    title_attr = f' title="{title}"' if title else ""
    return f'<a href="{href}" target="_blank" rel="noopener"{title_attr}><code>{text}</code></a>'


def _link_for_code(text: str) -> str | None:
    """Return a URL to link an inline <code>TEXT</code> to, or None."""
    if text in _DIRECTORY_LINKS:
        return _DIRECTORY_LINKS[text]
    m = _SCRIPT_RE.match(text)
    if m:
        return f"{REPO_BLOB}/scripts/{m.group(1)}"
    m = _GROUND_TRUTH_FILE_RE.match(text)
    if m:
        return f"{REPO_BLOB}/{text}"
    m = _OSM_TAG_RE.match(text)
    if m:
        k, v = m.group(1), m.group(2)
        return f"{OSM_WIKI}/Tag:{k}%3D{v}"
    if text in _BARE_LEISURE_VALUES:
        return f"{OSM_WIKI}/Tag:leisure%3D{text}"
    return None


def _linkify_inline_code(match: re.Match) -> str:
    text = match.group(1)
    # Compound tags like `leisure=pitch + sport=tennis` — link each K=V part
    # individually inside the <code> block so the surrounding code styling is
    # preserved as a single unit.
    if _OSM_COMPOUND_TAG_RE.match(text):
        def _wrap_token(tm: re.Match) -> str:
            k, v = tm.group(1), tm.group(2)
            return (
                f'<a href="{OSM_WIKI}/Tag:{k}%3D{v}" '
                f'target="_blank" rel="noopener">{tm.group(0)}</a>'
            )
        inner = _OSM_TAG_TOKEN_RE.sub(_wrap_token, text)
        return f"<code>{inner}</code>"
    href = _link_for_code(text)
    if href is None:
        return match.group(0)
    return _wrap_code(text, href)


def _linkify_pre_block(match: re.Match) -> str:
    body = match.group(1)
    lines = body.splitlines()
    non_empty = [ln.strip() for ln in lines if ln.strip()]
    if not non_empty or not all(_PRE_GROUND_TRUTH_LINE_RE.match(ln) for ln in non_empty):
        return match.group(0)
    new_lines = []
    for ln in lines:
        stripped = ln.strip()
        if stripped:
            href = f"{REPO_BLOB}/{stripped}"
            new_lines.append(
                f'<a href="{href}" target="_blank" rel="noopener">{ln}</a>'
            )
        else:
            new_lines.append(ln)
    return f"<pre><code>{chr(10).join(new_lines)}</code></pre>"


def linkify_html(html: str) -> str:
    """Wrap asset references (scripts, data files, ground-truth reports, OSM tags,
    the repo root path) in clickable links pointing at the canonical source on
    GitHub or the OpenStreetMap wiki. Idempotent on text without matching codes."""
    # 1) Multi-line <pre><code> ground-truth listing — link each line.
    html = re.sub(
        r"<pre><code>([^<]*)</code></pre>",
        _linkify_pre_block,
        html,
        flags=re.DOTALL,
    )
    # 2) Mask out any remaining <pre>...</pre> so step 3 doesn't double-wrap.
    pre_blocks: list[str] = []

    def _stash(m: re.Match) -> str:
        pre_blocks.append(m.group(0))
        return f"\x00PRE{len(pre_blocks) - 1}\x00"

    html = re.sub(r"<pre>.*?</pre>", _stash, html, flags=re.DOTALL)
    # 3) Inline <code>...</code> — link if it matches a known asset pattern.
    html = re.sub(r"<code>([^<]+)</code>", _linkify_inline_code, html)
    # 4) Restore the masked <pre> blocks.
    for i, block in enumerate(pre_blocks):
        html = html.replace(f"\x00PRE{i}\x00", block)
    return html


GITHUB_ICON_SVG = (
    '<svg class="gh-icon" xmlns="http://www.w3.org/2000/svg" width="16" '
    'height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">'
    '<path d="M12 .5a11.5 11.5 0 0 0-3.64 22.42c.58.1.79-.25.79-.56v-2c-3.2.7-3.88-1.37-3.88-1.37-.53-1.36-1.3-1.72-1.3-1.72-1.07-.73.08-.71.08-.71 1.18.08 1.8 1.22 1.8 1.22 1.05 1.8 2.75 1.28 3.42.98.1-.77.41-1.28.75-1.57-2.55-.29-5.24-1.28-5.24-5.7 0-1.26.45-2.3 1.19-3.1-.12-.3-.51-1.5.11-3.12 0 0 .97-.31 3.18 1.18a11 11 0 0 1 5.79 0c2.2-1.49 3.17-1.18 3.17-1.18.63 1.62.24 2.82.12 3.12.74.8 1.18 1.84 1.18 3.1 0 4.43-2.69 5.4-5.25 5.69.42.36.8 1.08.8 2.18v3.23c0 .31.21.67.8.56A11.5 11.5 0 0 0 12 .5z"/>'
    "</svg>"
)


def repo_banner() -> str:
    return (
        '<nav class="repo-banner" role="navigation" aria-label="Report navigation">'
        f'<a href="{REPO_URL}" target="_blank" rel="noopener">'
        f'{GITHUB_ICON_SVG}View source on GitHub</a>'
        '<span class="sep">·</span>'
        f'<a href="{PDF_HREF}">Download PDF</a>'
        '<span class="sep">·</span>'
        f'<a href="{REPO_TREE}/reports">Reports &amp; charts</a>'
        '<span class="sep">·</span>'
        f'<a href="{REPO_TREE}/reports/ground_truth">Per-city audits</a>'
        '<span class="sep">·</span>'
        f'<a href="{REPO_TREE}/scripts">Pipeline scripts</a>'
        '<span class="sep">·</span>'
        f'<a href="{REPO_TREE}/data/processed">Processed data</a>'
        '</nav>'
    )


def repo_footer() -> str:
    return (
        '<footer class="repo-footer">'
        f'<p>Source code, data and per-city audit reports: '
        f'<a href="{REPO_URL}" target="_blank" rel="noopener">'
        f'jameshartt/BHPLTA-densest-circle-report</a> on GitHub. '
        f'Headline figures: <a href="{REPO_BLOB}/data/processed/global_density_sea_corrected.csv">'
        'global_density_sea_corrected.csv</a> · '
        f'<a href="{REPO_BLOB}/data/processed/global_densest_circle.csv">'
        'global_densest_circle.csv</a> · '
        f'<a href="{REPO_BLOB}/data/processed/uk_density_final.csv">'
        'uk_density_final.csv</a>. '
        f'Rendered from <a href="{REPO_BLOB}/reports/densest_circle_full_writeup.md">'
        'reports/densest_circle_full_writeup.md</a> by '
        f'<a href="{REPO_BLOB}/scripts/27_pdf_report.py">scripts/27_pdf_report.py</a>.</p>'
        '</footer>'
    )


def build_html() -> str:
    md_text = MD_FILE.read_text()
    # Replace markdown image syntax with base64-embedded versions (so PDF is portable)
    md_text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", embed_image, md_text)
    body = md_to_html(md_text)
    body = linkify_html(body)
    html = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Brighton & Hove: densest park-tennis cluster in the world</title>
<link rel="canonical" href="{REPO_URL}">
<style>{CSS}</style>
</head>
<body>
{repo_banner()}
{body}
{repo_footer()}
</body>
</html>
"""
    return html


def main() -> int:
    HTML_FILE.write_text(build_html())
    print(f"wrote {HTML_FILE}")

    # Use Chrome to print to PDF
    cmd = [
        "google-chrome",
        "--headless=new",
        "--no-sandbox",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={PDF_FILE}",
        f"file://{HTML_FILE}",
    ]
    print("Running:", " ".join(cmd))
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if res.returncode != 0:
        print("Chrome stderr:", res.stderr[-2000:])
        print("Chrome stdout:", res.stdout[-1000:])
        return res.returncode
    print(f"wrote {PDF_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
