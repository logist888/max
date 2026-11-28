"""Render Markdown reports through WeasyPrint with paged print styles."""
import argparse
import subprocess
import tempfile
from pathlib import Path

CSS = """
@page { size: A4; margin: 15mm 15mm 16mm; }
html { font-family: "Golos Text","Noto Sans","Noto Sans CJK SC","Noto Sans Arabic",sans-serif;
  color: #16283e; font-size: 9.3pt; line-height: 1.47; }
body { max-width: 100%; padding: 0; margin: 0; }
h1 { font-size: 28pt; letter-spacing: -.025em; color: #163660; line-height: 1.14; margin: 0 0 18pt; border-top: 3pt solid #2d66ab; padding-top: 18pt; }
h2 { color:#163660; line-height:1.18; font-size:16pt; margin:18pt 0 7pt; break-after:avoid; border-bottom:.5pt solid #d8e2ef; padding-bottom:4pt; }
h3,h4 { color:#25588c; line-height:1.26; margin:12pt 0 5pt; break-after:avoid; }
p,li { orphans:2; widows:2; overflow-wrap:anywhere; }
ol,ul { padding-left:16pt; }
table { border-collapse:collapse; width:100%; table-layout:auto; margin: 7pt 0 11pt; font-size:8pt; line-height:1.28; }
thead { display:table-header-group; }
th { text-align:left; color:#163660; background:#dce8f5; font-weight:700; }
td,th { padding:4.1pt 4.5pt; vertical-align:top; border-bottom:.6pt solid #d9e3ef; overflow-wrap:anywhere; word-break:normal; }
tbody tr:nth-child(2n) { background:#f4f7fb; }
small { font-size:8pt; }
code { font-family:"Noto Sans Mono","Noto Sans CJK SC",monospace; font-size:.9em; overflow-wrap:anywhere; }
pre { background:#edf3fa; border-left:2pt solid #91afcf; white-space:pre-wrap; overflow-wrap:anywhere; padding:8pt; }
a { color:#1b5a97; text-decoration:none; }
blockquote { margin:8pt 0; padding:2pt 9pt; border-left:2pt solid #86afd4; background:#edf4fc; }
body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
.wide { font-size: 7.6pt; }
"""
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    p.add_argument("--wide",action="store_true")
    a=p.parse_args()
    with tempfile.TemporaryDirectory() as d:
        tmp=Path(d)
        css=tmp/"report.css"
        css.write_text(CSS + ("\n@page { size: A4 landscape; }" if a.wide else ""))
        path=tmp/"report.html"
        subprocess.run(["pandoc",str(a.source),"--from=gfm","--to=html5","--standalone","--embed-resources",
                        f"--css={css}","--metadata","pagetitle=MainExperts · Исследование v4.0","-o",str(path)],
                       check=True,capture_output=True)
        a.output.parent.mkdir(parents=True,exist_ok=True)
        from weasyprint import HTML
        HTML(filename=str(path)).write_pdf(a.output)
        if not a.output.exists() or a.output.stat().st_size<2000:
            raise RuntimeError("No complete PDF received")
if __name__=="__main__":
    main()
