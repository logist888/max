# -*- coding: utf-8 -*-
"""Необязательный экспорт в PNG, PDF и HTML. PNG и PDF требуют Playwright (pip install playwright; playwright install chromium)."""
import os
import re


def _size(svg_path):
    with open(svg_path, encoding="utf-8") as fh:
        head = fh.read(600)
    m = re.search(r'width="(\d+)" height="(\d+)"', head)
    return int(m.group(1)), int(m.group(2))


def write_html(svg_path, html_path, title):
    with open(svg_path, encoding="utf-8") as fh:
        svg = fh.read().split("?>", 1)[-1]
    page = """<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s</title><style>
body{margin:0;background:#fff;font:14px Inter,Arial,sans-serif}
#bar{position:fixed;top:8px;left:8px;z-index:5;display:flex;gap:6px}
#bar button{font:600 14px Inter,Arial,sans-serif;padding:6px 12px;border:1px solid #888;background:#fff;border-radius:4px;cursor:pointer}
#wrap{overflow:auto;width:100vw;height:100vh}#wrap svg{display:block;transform-origin:0 0}
</style></head><body><div id="bar"><button id="o">−</button><button id="i">+</button><button id="f">Вписать</button><button id="r">100%%</button></div>
<div id="wrap">%s</div><script>
const w=document.getElementById('wrap'),s=w.querySelector('svg'),W=+s.getAttribute('width'),H=+s.getAttribute('height');let k=1;
function set(v){k=Math.max(.03,Math.min(3,v));s.style.width=W*k+'px';s.style.height=H*k+'px'}
document.getElementById('i').onclick=()=>set(k*1.25);document.getElementById('o').onclick=()=>set(k/1.25);
document.getElementById('r').onclick=()=>set(1);document.getElementById('f').onclick=()=>set(innerWidth/W);
w.addEventListener('wheel',e=>{if(e.ctrlKey||e.metaKey){e.preventDefault();set(k*(e.deltaY<0?1.1:1/1.1))}},{passive:false});
set(Math.min(1,innerWidth/W));
</script></body></html>""" % (title.replace("<", "&lt;"), svg)
    with open(html_path, "w", encoding="utf-8") as fh:
        fh.write(page)


def write_png_pdf(svg_path, out_dir, want_png, want_pdf):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return ["PNG/PDF пропущены: нет Playwright (pip install playwright && playwright install chromium)"]
    W, H = _size(svg_path)
    done = []
    with sync_playwright() as p:
        b = None
        errors = []
        for exe in (None, os.environ.get("CJM_CHROMIUM"), "/opt/pw-browsers/chromium"):
            if exe is None and errors:
                continue
            if exe is not None and not os.path.exists(exe):
                continue
            try:
                b = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
                break
            except Exception as ex:  # браузер не найден или не запускается
                errors.append(str(ex).splitlines()[0])
        if b is None:
            return ["PNG/PDF пропущены: браузер Playwright не запустился (%s). Выполните «playwright install chromium» или задайте CJM_CHROMIUM" % (errors[0] if errors else "нет браузера")]
        try:
            def shot(width, name):
                h = max(1, round(H * width / W))
                pg = b.new_page(viewport={"width": width, "height": h})
                pg.set_content('<body style="margin:0"><img id="m" style="display:block;width:%dpx;height:%dpx"></body>' % (width, h))
                with open(svg_path, "rb") as fh:
                    import base64
                    data = base64.b64encode(fh.read()).decode()
                pg.evaluate("src=>{const i=document.getElementById('m');i.src=src;return new Promise(r=>{i.onload=r})}", "data:image/svg+xml;base64," + data)
                pg.screenshot(path=os.path.join(out_dir, name), full_page=True)
                pg.close()
                done.append(name)
            if want_png:
                shot(min(W, 4000), "map.png")
                shot(8000, "map-8000px.png")
            if want_pdf:
                k = min(1.0, 18000.0 / W)
                pw, ph = int(W * k), int(H * k)
                pg = b.new_page()
                with open(svg_path, "rb") as fh:
                    import base64
                    data = base64.b64encode(fh.read()).decode()
                pg.set_content('<body style="margin:0"><img style="display:block;width:%dpx;height:%dpx" src="data:image/svg+xml;base64,%s"></body>' % (pw, ph, data))
                pg.wait_for_timeout(500)
                pg.pdf(path=os.path.join(out_dir, "map.pdf"), width="%dpx" % pw, height="%dpx" % ph, print_background=True)
                pg.close()
                done.append("map.pdf")
        finally:
            b.close()
    return done
