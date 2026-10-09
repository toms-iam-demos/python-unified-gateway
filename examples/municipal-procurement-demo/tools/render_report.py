"""Optional authoring tool: pip install pypandoc_binary. Not a runtime dependency."""

from pathlib import Path
import re
import pypandoc

root = Path(__file__).resolve().parents[1]
docs = root / "docs"
s = (docs / "Municipal-Procurement-IAM-Technical-Report.tex").read_text(encoding="utf-8")
# HTML uses the exact report prose and pre-rendered diagrams rather than inline TikZ.
s = re.sub(r"\\begin\{titlepage\}.*?\\end\{titlepage\}", "", s, flags=re.S)
s = s.replace(r"\tableofcontents\newpage", "")
for name in ("architecture", "command", "delivery"):
    s = re.sub(
        r"\\begin\{figure\}.*?\\end\{figure\}",
        lambda m: r"\includegraphics{" + name + ".svg}",
        s,
        count=1,
        flags=re.S,
    )
s = re.sub(r"\\src\{(S\d+)\}", lambda m: "[" + m[1] + "]", s)
s = re.sub(r"\\newcommand\{\\src\}.*?\n", "", s)
s = s.replace("\\code{", "\\texttt{")
body = pypandoc.convert_text(
    s,
    "html5",
    format="latex",
    extra_args=["--mathml", "--wrap=none", "--shift-heading-level-by=1"],
)
body = re.sub(
    r"\[(S\d+)\]", lambda m: '<a href="#src:' + m[1] + '">[' + m[1] + "]</a>", body
)
html = (
    """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Municipal procurement | Technical report</title><link rel="stylesheet" href="report.css"></head><body><header><a href="/">← Return to the demonstration</a><p>PUG / RESEARCH + ENGINEERING / 07 OCT 2026</p><h1>Municipal procurement intelligence</h1><p>From agreement to accountability.</p><a href="Municipal-Procurement-IAM-Technical-Report.tex" download>Download the canonical LaTeX source</a></header><main><aside>Independent concept. Synthetic data. No city endorsement or live provider connection.</aside>"""
    + body
    + """</main><footer>PUG • Portable procurement demonstration • Synthetic design with explicit limitations</footer></body></html>"""
)
(docs / "report.html").write_text(html, encoding="utf-8")
print("HTML report generated from canonical LaTeX source")
