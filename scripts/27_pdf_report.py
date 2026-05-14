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
"""


def md_to_html(md_text: str) -> str:
    body_html = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "toc"],
    )
    return body_html


def embed_image(match: re.Match) -> str:
    """Convert markdown image references to inline base64 (for PDF self-containment)."""
    alt = match.group(1)
    path_str = match.group(2)
    p = (REPORTS / path_str).resolve()
    if not p.exists():
        return f'<em>(missing image: {path_str})</em>'
    data = p.read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    suffix = p.suffix.lstrip(".").lower()
    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "svg": "image/svg+xml"}.get(suffix, "image/png")
    return f'<img alt="{alt}" src="data:{mime};base64,{b64}">'


def build_html() -> str:
    md_text = MD_FILE.read_text()
    # Replace markdown image syntax with base64-embedded versions (so PDF is portable)
    md_text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", embed_image, md_text)
    body = md_to_html(md_text)
    html = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Brighton & Hove: densest park-tennis cluster in the world</title>
<style>{CSS}</style>
</head>
<body>
{body}
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
