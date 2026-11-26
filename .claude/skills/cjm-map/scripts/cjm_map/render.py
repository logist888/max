# -*- coding: utf-8 -*-
"""Раскладка и отрисовка карты: блок-схема с дорожками сверху, под ней столбцы CJM в тех же колонках.

Вся геометрия считается здесь, браузер не нужен. Два режима текста:
  outline — буквы контурами (файл одинаково открывается в Figma, Miro, Illustrator, на телефоне);
  text    — обычные <text> (выделяются, ищутся).
"""
import base64
import html
import math
import os
import struct

from . import fonts

DX = 215.0                 # ширина колонки
LAB = 122.5                # ширина колонки подписей слева
X0 = LAB + DX / 2          # центр колонки 0
GAP = 6                    # зазор между рядами
STK_W = 176.0              # ширина стикера
FONT = "Inter,'Segoe UI',Arial,'DejaVu Sans',sans-serif"
ROT = [-1.1, 0.7, -0.4, 1.0, 0.2, -0.8, 0.5]
YEL = ["#fff59d", "#ffee77", "#ffe38a", "#fff9c4"]
KIND_FILL = {"g": "#a7e38c", "r": "#f59a9a", "o": "#ffb674", "b": "#7fd2f5", "w": "#ffffff", "gr": "#dcdcdc",
             "ey": "#ffd84d", "ghost": "#fff59d"}
LANE_STYLE = {0: ("#fff3a8", "#a58f12"), 1: ("#d4f0fb", "#2a8fbd"), 2: ("#dbe6ff", "#4a6fd0"), 3: ("#d8f3dc", "#3f9a55"),
              4: ("#eadcf8", "#8a5cc0"), 5: ("#ffe4cc", "#d08a3a"), 6: ("#ececec", "#6f6f6f")}
STAGE_COLOR = {"cyan": "#12c4d4", "blue": "#0f7de6"}
# ширина, внутренняя ширина текста, минимальная высота, добавка к высоте
SHAPES = {"term": (176, 148, 54, 22), "proc": (164, 148, 62, 20), "dec": (172, 104, 104, 52), "data": (176, 122, 62, 20),
          "doc": (164, 146, 66, 28), "manual": (170, 126, 62, 22), "db": (124, 108, 78, 24), "pre": (160, 118, 62, 20),
          "note": (176, 156, 50, 18)}
LEGEND_SHAPES = [("term", "Начало или конец"), ("proc", "Действие, шаг процесса"), ("dec", "Решение, развилка"),
                 ("data", "Ввод или вывод данных клиентом"), ("doc", "Документ, результат"), ("db", "База данных"),
                 ("manual", "Ручная операция"), ("pre", "Предопределённый процесс (подпроцесс правее)"), ("note", "Примечание")]
LEGEND_CHIPS = [("g", "Драйвер или хороший опыт"), ("r", "Барьер или риск, который остаётся"), ("y", "Шаг, мысль, идея"),
                ("b", "Ключевой переход или вставка в поиске"), ("ghost", "Гипотеза, не подтверждённая данными"),
                ("gr", "Пояснение"), ("g", "Положительная эмоция"), ("ey", "Нейтральная"), ("r", "Отрицательная")]
HOW_TO_READ = ("Как читать: сверху блок-схема, под ней стикеры в тех же колонках. Стрелки между стикерами повторяют ход "
               "процесса; точечная линия в эмоциях — кривая настроения.")


def e(s):
    return html.escape(str(s), quote=True)


def fmt(v):
    return ("%.1f" % v).rstrip("0").rstrip(".")


# ---------------------------------------------------------------- холст
class Canvas:
    LAYERS = ("bg", "screens", "flow", "arrows", "stickies")

    def __init__(self, mode):
        self.mode = mode
        self.layers = {k: [] for k in self.LAYERS}
        self.cur = "bg"

    def use(self, name):
        self.cur = name

    def raw(self, s):
        if s:
            self.layers[self.cur].append(s)

    def rect(self, x, y, w, h, fill, rx=0, extra=""):
        self.raw('<rect x="%s" y="%s" width="%s" height="%s"%s fill="%s"%s/>' % (
            fmt(x), fmt(y), fmt(w), fmt(h), (' rx="%s"' % fmt(rx)) if rx else "", fill, extra))

    def text(self, x, y, s, size, weight, fill, anchor="start", stroke=None, sw=0):
        if not s:
            return
        if self.mode == "outline":
            self.raw(fonts.outline(s, x, y, size, weight, fill, anchor, stroke, sw))
        else:
            halo = (' stroke="%s" stroke-width="%s" stroke-linejoin="round" paint-order="stroke"' % (stroke, sw)) if stroke else ""
            self.raw('<text x="%s" y="%s" font-size="%s" font-weight="%s" fill="%s"%s%s>%s</text>' % (
                fmt(x), fmt(y), fmt(size), weight, fill, (' text-anchor="%s"' % anchor) if anchor != "start" else "", halo, e(s)))

    def lines(self, x, y_first, lines, size, weight, fill, lh, anchor="start"):
        for i, ln in enumerate(lines):
            self.text(x, y_first + i * lh, ln, size, weight, fill, anchor)

    def arrow_head(self, pts, color, size=11.0):
        (x2, y2) = pts[-1]
        prev = None
        for p in reversed(pts[:-1]):
            if abs(p[0] - x2) + abs(p[1] - y2) > 0.5:
                prev = p
                break
        if prev is None:
            return
        dx, dy = x2 - prev[0], y2 - prev[1]
        L = math.hypot(dx, dy) or 1
        ux, uy = dx / L, dy / L
        k = size / 10.0
        tip = (x2 + ux * k, y2 + uy * k)
        bx, by = tip[0] - ux * 10 * k, tip[1] - uy * 10 * k
        nx, ny = -uy, ux
        a = (bx + nx * 5 * k, by + ny * 5 * k)
        b = (bx - nx * 5 * k, by - ny * 5 * k)
        self.raw('<polygon points="%s,%s %s,%s %s,%s" fill="%s"/>' % (fmt(tip[0]), fmt(tip[1]), fmt(a[0]), fmt(a[1]), fmt(b[0]), fmt(b[1]), color))

    def done(self, W, H, title, desc):
        body = []
        ids = {"bg": "backgrounds", "screens": "screens", "flow": "flowchart", "arrows": "arrows", "stickies": "stickies"}
        for k in self.LAYERS:
            body.append('<g id="%s">%s</g>' % (ids[k], "".join(self.layers[k])))
        fam = ' font-family="%s"' % e(FONT) if self.mode == "text" else ""
        return ('<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d"%s>\n'
                '<title>%s</title>\n<desc>%s</desc>\n<rect width="%d" height="%d" fill="#ffffff"/>\n%s\n</svg>\n') % (
            W, H, W, H, fam, e(title), e(desc), W, H, "\n".join(body))


# ---------------------------------------------------------------- блок-схема
class Node:
    def __init__(self, d, lane_idx, style_idx):
        self.id, self.shape, self.col, self.text = d["id"], d["shape"], d["col"], d["text"]
        self.lane, self.dy, self.hyp, self.style = lane_idx, d.get("dy", 0), bool(d.get("hypothesis")), style_idx
        w, tw, mh, add = SHAPES[self.shape]
        self.w = w
        self.lines = fonts.wrap(self.text, 11, 400, tw)
        self.h = max(mh, len(self.lines) * 13 + add)
        self.x = self.y = 0.0

    def place(self, x, y):
        self.x, self.y = x, y

    def port(self, p):
        skew = 16 if self.shape in ("data", "manual") else 0
        if p == "l":
            return (self.x - self.w / 2 + skew / 2, self.y)
        if p == "r":
            return (self.x + self.w / 2 - skew / 2, self.y)
        if p == "t":
            return (self.x, self.y - self.h / 2)
        return (self.x, self.y + self.h / 2)


def rounded(pts, r=9):
    if len(pts) < 3:
        return "M%s %s L%s %s" % (fmt(pts[0][0]), fmt(pts[0][1]), fmt(pts[-1][0]), fmt(pts[-1][1]))
    d = "M%s %s" % (fmt(pts[0][0]), fmt(pts[0][1]))
    for i in range(1, len(pts) - 1):
        p0, p1, p2 = pts[i - 1], pts[i], pts[i + 1]

        def toward(a, b, from_a):
            dx, dy = b[0] - a[0], b[1] - a[1]
            L = math.hypot(dx, dy) or 1
            k = min(r, L / 2) / L
            return (a[0] + dx * k, a[1] + dy * k) if from_a else (b[0] - dx * k, b[1] - dy * k)

        a = toward(p0, p1, False)
        b = toward(p1, p2, True)
        d += " L%s %s Q%s %s %s %s" % (fmt(a[0]), fmt(a[1]), fmt(p1[0]), fmt(p1[1]), fmt(b[0]), fmt(b[1]))
    return d + " L%s %s" % (fmt(pts[-1][0]), fmt(pts[-1][1]))


def route(a, sp, b, dp, corridor_y=None, near=False):
    p1, p2 = a.port(sp), b.port(dp)
    if corridor_y is not None:
        return [p1, (p1[0], corridor_y), (p2[0], corridor_y), p2]
    (x1, y1), (x2, y2) = p1, p2
    k = sp + dp
    if k == "rl":
        if abs(y1 - y2) < 1:
            return [p1, p2]
        xm = (x2 - 25) if (near and x2 - x1 > 100) else (x1 + x2) / 2
        return [p1, (xm, y1), (xm, y2), p2]
    if k in ("rt", "rb"):
        return [p1, (x2, y1), p2]
    if k in ("bl", "tl"):
        return [p1, (x1, y2), p2]
    if k in ("lb", "lt"):
        return [p1, (x2, y1), p2]
    if k in ("bt", "tb"):
        if abs(x1 - x2) < 1:
            return [p1, p2]
        ym = (y1 + y2) / 2
        return [p1, (x1, ym), (x2, ym), p2]
    if k == "lr":
        return [p1, p2] if abs(y1 - y2) < 1 else [p1, (x1, y2), p2]
    return [p1, p2]


def auto_ports(a, b):
    if b.x > a.x + 5:
        return "rl"
    if b.x < a.x - 5:
        return "lr"
    return "bt" if b.y >= a.y else "tb"


def draw_shape(c, n):
    x, y, w, h = n.x, n.y, n.w, n.h
    fill, stroke = LANE_STYLE[n.style]
    dash = ' stroke-dasharray="6 4"' if n.hyp else ""
    base = 'fill="%s" stroke="%s" stroke-width="1.6"%s' % (fill, stroke, dash)
    P = lambda *v: " ".join(fmt(t) for t in v)
    s = ""
    if n.shape == "term":
        s = '<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="#2b2b2b" stroke="#111" stroke-width="1.6"/>' % (fmt(x - w / 2), fmt(y - h / 2), fmt(w), fmt(h), fmt(h / 2))
    elif n.shape == "proc":
        s = '<rect x="%s" y="%s" width="%s" height="%s" rx="3" %s/>' % (fmt(x - w / 2), fmt(y - h / 2), fmt(w), fmt(h), base)
    elif n.shape == "dec":
        s = '<polygon points="%s,%s %s,%s %s,%s %s,%s" %s/>' % (fmt(x), fmt(y - h / 2), fmt(x + w / 2), fmt(y), fmt(x), fmt(y + h / 2), fmt(x - w / 2), fmt(y), base)
    elif n.shape in ("data", "manual"):
        k = 16
        if n.shape == "data":
            pts = [(x - w / 2 + k, y - h / 2), (x + w / 2, y - h / 2), (x + w / 2 - k, y + h / 2), (x - w / 2, y + h / 2)]
        else:
            pts = [(x - w / 2, y - h / 2), (x + w / 2, y - h / 2), (x + w / 2 - k, y + h / 2), (x - w / 2 + k, y + h / 2)]
        s = '<polygon points="%s" %s/>' % (" ".join("%s,%s" % (fmt(a), fmt(b)) for a, b in pts), base)
    elif n.shape == "doc":
        t, b, l, r = y - h / 2, y + h / 2, x - w / 2, x + w / 2
        s = '<path d="M%s H%s V%s C%s,%s,%s C%s,%s,%s Z" %s/>' % (
            P(l, t), fmt(r), fmt(b - 8), P(r - w * .25, b - 20), P(r - w * .5, b + 4), P(x, b - 8),
            P(x - w * .25, b - 20), P(l, b + 2), P(l, b - 8), base)
    elif n.shape == "db":
        l, r, t, b = x - w / 2, x + w / 2, y - h / 2, y + h / 2
        ry = 9
        s = ('<path d="M%s V%s A%s %s 0 0 0 %s V%s A%s %s 0 0 0 %s Z" %s/>' % (
            P(l, t + ry), fmt(b - ry), fmt(w / 2), fmt(ry), P(r, b - ry), fmt(t + ry), fmt(w / 2), fmt(ry), P(l, t + ry), base))
        s += '<ellipse cx="%s" cy="%s" rx="%s" ry="%d" %s/>' % (fmt(x), fmt(t + ry), fmt(w / 2), ry, base)
    elif n.shape == "pre":
        s = '<rect x="%s" y="%s" width="%s" height="%s" rx="2" %s/>' % (fmt(x - w / 2), fmt(y - h / 2), fmt(w), fmt(h), base)
        for xx in (x - w / 2 + 12, x + w / 2 - 12):
            s += '<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="1.6"/>' % (fmt(xx), fmt(y - h / 2), fmt(xx), fmt(y + h / 2), stroke)
    elif n.shape == "note":
        t, b, l, r = y - h / 2, y + h / 2, x - w / 2, x + w / 2
        s = '<path d="M%s H%s L%s V%s H%s Z" fill="#fffbe0" stroke="#b9a93a" stroke-width="1.2" stroke-dasharray="4 3"/>' % (P(l, t), fmt(r - 12), P(r, t + 12), fmt(b), fmt(l))
    c.raw(s)
    col = "#ffffff" if n.shape == "term" else "#1d1d1d"
    ty = y - (len(n.lines) - 1) * 6.5 + 4
    for i, ln in enumerate(n.lines):
        c.text(x, ty + i * 13, ln, 11, 400, col, "middle")


class Flow:
    def __init__(self, doc, y_top, W):
        self.doc, self.y_top, self.W = doc, y_top, W
        self.lanes = doc["lanes"]
        self.lane_idx = {ln["id"]: i for i, ln in enumerate(self.lanes)}
        self.lane_h = float(doc["flow"].get("lane_height", 240))
        self.body_top = y_top + 58 + 46
        self.nodes = {}
        self.order = []
        for d in doc["flow"]["nodes"]:
            li = self.lane_idx[d["lane"]]
            st = self.lanes[self.lane_idx[d["style"]]]["style"] if d.get("style") else self.lanes[li]["style"]
            n = Node(d, li, st)
            n.place(X0 + n.col * DX, self.body_top + li * self.lane_h + self.lane_h / 2 + n.dy)
            self.nodes[n.id] = n
            self.order.append(n)
        self.height = 58 + 46 + self.lane_h * len(self.lanes) + 20

    def lane_y(self, i):
        return self.body_top + i * self.lane_h + self.lane_h / 2

    def draw(self, c):
        doc = self.doc
        top = self.y_top
        c.use("flow")
        c.rect(0, top, self.W, self.height, "#ffffff")
        meta = doc["meta"]
        c.text(24, top + 26, meta.get("flow_title") or meta["title"], 18, 700, "#1d1d1d")
        sub = meta.get("subtitle")
        if sub:
            lines = fonts.wrap(sub, 12, 400, self.W - 48)
            c.text(24, top + 46, lines[0] + ("…" if len(lines) > 1 else ""), 12, 400, "#555555")
        for i, ln in enumerate(self.lanes):
            y = self.body_top + i * self.lane_h
            c.rect(0, y, self.W, self.lane_h, "#fafafa" if i % 2 == 0 else "#f0f0f0")
            c.rect(0, y, LAB, self.lane_h, "#7b7b7b")
            c.raw('<line x1="0" y1="%s" x2="%s" y2="%s" stroke="#cfcfcf"/>' % (fmt(y), fmt(self.W), fmt(y)))
            lines = fonts.wrap(ln["label"], 12.5, 400, LAB - 12)
            y0 = y + self.lane_h / 2 - (len(lines) - 1) * 8 + 4
            for j, t in enumerate(lines):
                c.text(LAB / 2, y0 + j * 16, t, 12.5, 400, "#ffffff", "middle")
        yb = self.body_top + len(self.lanes) * self.lane_h
        c.raw('<line x1="0" y1="%s" x2="%s" y2="%s" stroke="#cfcfcf"/>' % (fmt(yb), fmt(self.W), fmt(yb)))
        for s in doc["stages"]:
            x0 = LAB + s["from"] * DX + 4
            x1 = LAB + (s["to"] + 1) * DX - 4
            c.rect(x0, top + 58, x1 - x0, 34, STAGE_COLOR.get(s["color"], s["color"]))
            lab = s["label"]
            lines = fonts.wrap(lab, 14, 600, x1 - x0 - 16)
            if len(lines) > 1:
                lab = lines[0]
                while fonts.width(lab + "…", 14, 600) > x1 - x0 - 16 and len(lab) > 1:
                    lab = lab[:-1]
                lab += "…"
            c.text((x0 + x1) / 2, top + 80, lab, 14, 600, "#ffffff", "middle")
            c.raw('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="#b5b5b5" stroke-dasharray="3 5"/>' % (fmt(x0 - 4), fmt(top + 58), fmt(x0 - 4), fmt(yb)))
        for ed in doc["flow"].get("edges", []):
            a, b = self.nodes[ed["from"]], self.nodes[ed["to"]]
            ports = ed.get("ports") or auto_ports(a, b)
            cy = None
            if ed.get("corridor"):
                cy = self.lane_y(self.lane_idx[ed["corridor"]["lane"]]) + float(ed["corridor"]["dy"])
            pts = route(a, ports[0], b, ports[1], cy, ed.get("elbow") == "near")
            loss = ed.get("loss")
            col = "#d33333" if loss else ("#7a7a7a" if ed.get("dash") else "#333333")
            dash = ' stroke-dasharray="6 5"' if ed.get("dash") else ""
            c.raw('<path d="%s" fill="none" stroke="%s" stroke-width="1.6"%s/>' % (rounded(pts), col, dash))
            if ed.get("arrow", True):
                c.arrow_head(pts, col, 12.8)
            lab = ed.get("label")
            if lab:
                if ed.get("label_at") == "mid":
                    best, bl = 0, -1
                    for i in range(len(pts) - 1):
                        L = abs(pts[i + 1][0] - pts[i][0]) + abs(pts[i + 1][1] - pts[i][1])
                        if L > bl:
                            bl, best = L, i
                    lx = (pts[best][0] + pts[best + 1][0]) / 2
                    ly = (pts[best][1] + pts[best + 1][1]) / 2 - 7
                    anchor = "middle"
                else:
                    (x1_, y1_), (x2_, y2_) = pts[0], pts[1]
                    dx, dy = x2_ - x1_, y2_ - y1_
                    L = math.hypot(dx, dy) or 1
                    lx, ly = x1_ + dx / L * 22, y1_ + dy / L * 22
                    if abs(dy) > abs(dx):
                        lx += 15
                        anchor = "start"
                    else:
                        ly -= 7
                        anchor = "middle"
                c.text(lx, ly, lab, 11, 600, "#222222", anchor, stroke="#fafafa", sw=4)
        for n in self.order:
            draw_shape(c, n)


# ---------------------------------------------------------------- стикеры
class Sticky:
    def __init__(self, kind, text, idx, w=STK_W, size=12.5, pad_y=9, pad_x=10, min_h=0, sid=None):
        self.kind, self.text, self.sid, self.size = kind, text, sid, size
        self.weight = 600 if kind == "b" else 400
        self.lh = size * 1.32
        self.lines = fonts.wrap(text, size, self.weight, w - 2 * pad_x)
        self.w = w
        self.pad_x, self.pad_y = pad_x, pad_y
        self.h = max(min_h, 2 * pad_y + len(self.lines) * self.lh)
        self.fill = YEL[idx % 4] if kind == "y" else KIND_FILL[kind]
        self.angle = ROT[idx % len(ROT)]
        self.x = self.y = 0.0

    def place(self, x, y):
        self.x, self.y = x, y
        return self

    @property
    def cx(self):
        return self.x + self.w / 2

    @property
    def cy(self):
        return self.y + self.h / 2

    def draw(self, c, rotate=True):
        c.use("stickies")
        ang = self.angle if rotate else 0
        if abs(ang) > 0.01:
            c.raw('<g transform="rotate(%s %s %s)">' % (fmt(ang), fmt(self.cx), fmt(self.cy)))
        if self.kind == "ghost":
            c.rect(self.x, self.y, self.w, self.h, "#fff59d", 2, ' fill-opacity="0.45" stroke="#b9a93a" stroke-width="2" stroke-dasharray="6 4"')
        else:
            c.rect(self.x, self.y + 2, self.w, self.h, "#000000", 3, ' fill-opacity="0.16"')
            c.rect(self.x, self.y, self.w, self.h, self.fill, 2)
        base = self.y + self.pad_y + self.size * 0.97 + (self.lh - self.size * 1.21) / 2
        for i, ln in enumerate(self.lines):
            c.text(self.x + self.pad_x, base + i * self.lh, ln, self.size, self.weight, "#222222")
        if abs(ang) > 0.01:
            c.raw("</g>")


def flow_layout(items, avail, gap_x=10, gap_y=10, centered=True):
    """Раскладка стикеров переносом по строкам; возвращает (позиции относительно левого края, высота)."""
    per = max(1, int((avail + gap_x) // (STK_W + gap_x)))
    pos, y = [], 0.0
    for i in range(0, len(items), per):
        line = items[i:i + per]
        lw = sum(s.w for s in line) + gap_x * (len(line) - 1)
        x = (avail - lw) / 2 if centered else 0
        lh = max(s.h for s in line)
        for s in line:
            pos.append((s, x, y))
            x += s.w + gap_x
        y += lh + gap_y
    return pos, max(0.0, y - gap_y)


def image_size(path):
    with open(path, "rb") as fh:
        head = fh.read(26)
        if head[:8] == b"\x89PNG\r\n\x1a\n":
            return struct.unpack(">II", head[16:24])
        fh.seek(2)
        while True:
            b = fh.read(1)
            while b and b != b"\xff":
                b = fh.read(1)
            while b == b"\xff":
                b = fh.read(1)
            if not b:
                return None
            m = b[0]
            if 0xC0 <= m <= 0xCF and m not in (0xC4, 0xC8, 0xCC):
                fh.read(3)
                h, w = struct.unpack(">HH", fh.read(4))
                return w, h
            ln = struct.unpack(">H", fh.read(2))[0]
            fh.seek(ln - 2, 1)


# ---------------------------------------------------------------- вся карта
def build_svg(doc, mode):
    c = Canvas(mode)
    ncols = max(doc["_ncols"], 6)
    W = int(LAB + ncols * DX + 24)
    meta, header = doc["meta"], doc.get("header") or {}
    y = 0.0

    # ----- шапка карты -----
    span_w = min(ncols, 12) * DX
    inner = span_w - 36

    def head_row(label, h):
        nonlocal y
        c.use("bg")
        c.rect(0, y, W, h, "#f3f3f3")
        c.rect(0, y, LAB - GAP, h - GAP, "#7b7b7b")
        lines = fonts.wrap(label, 13, 400, LAB - GAP - 16)
        y0 = y + (h - GAP) / 2 - (len(lines) - 1) * 8.7 + 4.5
        for i, t in enumerate(lines):
            c.text((LAB - GAP) / 2, y0 + i * 17.2, t, 12.5, 400, "#ffffff", "middle")
        c.rect(LAB, y, span_w, h - GAP, "#e9e9e9")

    t_lines = fonts.wrap(meta["title"], 18, 600, inner)
    h = 28 + len(t_lines) * 23 + GAP
    head_row("Название CJM", h)
    c.lines(LAB + 18, y + 14 + 18 * 0.97 + 2, t_lines, 18, 600, "#222222", 23)
    y += h
    if header.get("job"):
        j = fonts.wrap(header["job"], 15, 400, inner)
        h = 28 + len(j) * 19.5 + GAP
        head_row("Job To Be Done", h)
        c.lines(LAB + 18, y + 14 + 15 * 0.97 + 2, j, 15, 400, "#222222", 19.5)
        y += h
    if header.get("assumption"):
        st = Sticky("y", header["assumption"], 1, w=min(1500, inner), size=14, pad_x=16, pad_y=12)
        h = 28 + st.h + GAP
        head_row("Допущение", h)
        st.place(LAB + 18, y + 14).draw(c, rotate=False)
        y += h
    if header.get("drivers") or header.get("barriers"):
        groups = []
        total = 0.0
        for kind, key, off in (("g", "drivers", 0), ("r", "barriers", 2)):
            items = [Sticky(kind, t, i + off) for i, t in enumerate(header.get(key) or [])]
            if items:
                pos, gh = flow_layout(items, inner, 12, 12, centered=False)
                groups.append((pos, total))
                total += gh + 12
        h = 28 + (total - 12) + GAP
        head_row("Драйверы и барьеры использования", h)
        for pos, off in groups:
            for s, px, py in pos:
                s.place(LAB + 18 + px, y + 14 + off + py).draw(c)
        y += h
    # условные обозначения
    chips = []
    cx, cy_, line_h = 0.0, 0.0, 26 + 14
    placed = []
    legend = [(l["kind"], l["text"]) for l in header["legend"]] if header.get("legend") else LEGEND_CHIPS
    how_text = header.get("how_to_read") or HOW_TO_READ
    for i, (k, t) in enumerate(legend):
        wch = fonts.width(t, 12, 400) + 24
        if cx + wch > inner and cx > 0:
            cx, cy_ = 0.0, cy_ + line_h
        placed.append((k, t, cx, cy_, wch, i))
        cx += wch + 14
    how = fonts.wrap(how_text, 12, 400, inner)
    cy_ += line_h
    h = 28 + cy_ + len(how) * 16 + GAP
    head_row("Условные обозначения", h)
    for (k, t, px, py, wch, i) in placed:
        fill = YEL[i % 4] if k == "y" else KIND_FILL[k]
        x0, y0 = LAB + 18 + px, y + 14 + py
        if k == "ghost":
            c.rect(x0, y0, wch, 26, "#fff59d", 2, ' fill-opacity="0.45" stroke="#b9a93a" stroke-width="2" stroke-dasharray="6 4"')
        else:
            c.rect(x0, y0, wch, 26, fill, 2)
        c.text(x0 + 12, y0 + 17, t, 12, 400, "#222222")
    c.lines(LAB + 18, y + 14 + cy_ + 12, how, 12, 400, "#222222", 16)
    y += h

    # ----- условные обозначения блок-схемы -----
    y += 4
    c.use("flow")
    c.rect(0, y, W, 8, "#ffffff")
    ly = y + 18
    c.text(24, ly, "Условные обозначения блок-схемы (нотация ГОСТ 19.701-90, ISO 5807)", 14, 700, "#1d1d1d")
    sx, sy, row_h = 130.0, ly + 70.0, 0.0
    for kind, text in LEGEND_SHAPES:
        n = Node({"id": "lg", "shape": kind, "col": 0, "text": text}, 0, 0)
        if sx + n.w / 2 > W - 40:
            sx, sy = 130.0, sy + row_h + 24
            row_h = 0
        n.place(sx, sy)
        draw_shape(c, n)
        row_h = max(row_h, n.h)
        sx += n.w + 36
    ys = sy + row_h / 2 + 40
    c.raw('<line x1="130" y1="%s" x2="220" y2="%s" stroke="#333" stroke-width="1.6"/>' % (fmt(ys), fmt(ys)))
    c.arrow_head([(130, ys), (220, ys)], "#333333", 12.8)
    c.text(230, ys + 4, "основной поток", 11, 400, "#222222")
    c.raw('<line x1="400" y1="%s" x2="490" y2="%s" stroke="#7a7a7a" stroke-width="1.6" stroke-dasharray="6 5"/>' % (fmt(ys), fmt(ys)))
    c.arrow_head([(400, ys), (490, ys)], "#7a7a7a", 12.8)
    c.text(500, ys + 4, "необязательный переход, возврат из подпроцесса", 11, 400, "#222222")
    c.raw('<line x1="880" y1="%s" x2="970" y2="%s" stroke="#d33333" stroke-width="1.6"/>' % (fmt(ys), fmt(ys)))
    c.arrow_head([(880, ys), (970, ys)], "#d33333", 12.8)
    c.text(980, ys + 4, "выход, потеря клиента", 11, 400, "#222222")
    lx, ly2 = 130.0, ys + 34
    for ln in doc["lanes"]:
        fill, stroke = LANE_STYLE[ln["style"]]
        wch = 34 + 8 + fonts.width(ln["label"], 11, 400) + 28
        if lx + wch > W - 24:
            lx, ly2 = 130.0, ly2 + 28
        c.raw('<rect x="%s" y="%s" width="34" height="20" fill="%s" stroke="%s" stroke-width="1.6"/>' % (fmt(lx), fmt(ly2 - 10), fill, stroke))
        c.text(lx + 42, ly2 + 4, ln["label"], 11, 400, "#222222")
        lx += wch
    wch = 34 + 8 + fonts.width("пунктирная рамка — гипотеза, не подтверждённая данными", 11, 400)
    if lx + wch > W - 24:
        lx, ly2 = 130.0, ly2 + 28
    c.raw('<rect x="%s" y="%s" width="34" height="20" fill="#ececec" stroke="#6f6f6f" stroke-width="1.6" stroke-dasharray="6 4"/>' % (fmt(lx), fmt(ly2 - 10)))
    c.text(lx + 42, ly2 + 4, "пунктирная рамка — гипотеза, не подтверждённая данными", 11, 400, "#222222")
    y = ly2 + 24

    # ----- полоса и блок-схема -----
    c.use("bg")
    c.rect(0, y + 10, W, 52, "#2b2b2b")
    c.text(24, y + 10 + 14 + 16 * 0.97 + 2, "Блок-схема: единый поток слева направо", 16, 600, "#ffffff")
    y += 62
    flow = Flow(doc, y, W)
    flow.draw(c)
    y += flow.height + 8
    c.use("bg")
    c.rect(0, y + 10, W, 52, "#0f7de6")
    c.text(24, y + 10 + 14 + 16 * 0.97 + 2, "Стикеры: те же колонки, что у схемы выше; каждый шаг клиента стоит под своим узлом", 16, 600, "#ffffff")
    y += 62

    # ----- доска CJM -----
    board_top = y
    stages = doc["stages"]
    rows = doc["rows"]
    by_row = {}
    for i, s in enumerate(doc.get("stickies", [])):
        by_row.setdefault(s["row"], []).append(s)
    colx = lambda col: LAB + col * DX
    mats = {}          # id -> Sticky
    drawn = []         # все стикеры в порядке отрисовки
    emotions = []
    bg_idx = len(c.layers["bg"])
    labels = []
    # строка этапов
    sh = 0.0
    stage_lines = []
    for s in stages:
        wst = (s["to"] - s["from"] + 1) * DX - GAP
        ln = fonts.wrap(s["board_label"], 14, 600, wst - 24)
        stage_lines.append(ln)
        sh = max(sh, 20 + len(ln) * 18)
    sh = max(sh, 40)
    c.use("bg")
    c.rect(0, y, W, sh + GAP, "#f3f3f3")
    labels.append((y, sh, "Слои / Этапы"))
    for s, ln in zip(stages, stage_lines):
        wst = (s["to"] - s["from"] + 1) * DX - GAP
        x0 = colx(s["from"]) + GAP
        c.rect(x0, y, wst, sh, STAGE_COLOR.get(s["color"], s["color"]))
        c.lines(x0 + wst / 2, y + sh / 2 - (len(ln) - 1) * 9 + 5, ln, 14, 600, "#ffffff", 18, "middle")
    y += sh + GAP
    screens = doc.get("screens", [])
    for r in rows:
        rid, rtype = r["id"], r.get("type", "stack")
        items = by_row.get(rid, [])
        row_y = y
        rh_min = len(fonts.wrap(r["label"], 12.5, 400, LAB - GAP - 12)) * 17.2 + 24   # подпись ряда должна поместиться
        c.use("bg")
        if rtype == "emotion":
            rh = max(230.0, rh_min + GAP)
            third = (rh - GAP) / 3
            for i, colr in enumerate(("#eaf5e4", "#fdf3cf", "#f9e3e3")):
                c.rect(LAB, row_y + i * third, ncols * DX, third + 0.5, colr)
            for it in items:
                s = Sticky(it["kind"], it["text"], it["col"], sid=it.get("id"))
                top = {1: 8, 0: 84, -1: 160}[int(it["level"])]
                s.place(colx(it["col"]) + 12, row_y + top)
                emotions.append(s)
                drawn.append(s)
                if it.get("id"):
                    mats[it["id"]] = s
        elif rtype == "goal":
            heights = []
            blocks = []
            for st in stages:
                its = [Sticky(it["kind"], it["text"], k + 1, sid=it.get("id")) for k, it in enumerate(items) if it["stage"] == st["id"]]
                if not its:
                    continue
                avail = (st["to"] - st["from"] + 1) * DX - GAP - 24
                pos, gh = flow_layout(its, avail)
                blocks.append((st, pos))
                heights.append(gh + 24)
            rh = max(heights + [56, rh_min]) + GAP
            c.rect(LAB, row_y, ncols * DX, rh - GAP, "#e9e9e9")
            for st in stages:
                c.rect(colx(st["from"]), row_y, GAP, rh - GAP, "#f3f3f3")
            for st, pos in blocks:
                for s, px, py in pos:
                    s.place(colx(st["from"]) + GAP + 12 + px, row_y + 12 + py)
                    drawn.append(s)
                    if s.sid:
                        mats[s.sid] = s
        elif rtype == "screens":
            figs = []
            fh = 0.0
            for sc in screens:
                wfig = sc.get("span", 2) * DX - 16
                path = os.path.join(doc["_base"], sc["image"])
                size = image_size(path) if os.path.exists(path) else None
                ih = (wfig - 2) * size[1] / size[0] if size else (wfig - 2) * 0.62
                cap = fonts.wrap("%d. %s" % (len(figs) + 1, sc["caption"]), 12, 600, wfig - 18)
                hfig = 1 + ih + 7 + len(cap) * 15.6 + 9 + 1
                figs.append((sc, wfig, ih, cap, hfig, path if size else None))
                fh = max(fh, hfig)
            rh = max(fh + 24 if figs else 56, rh_min) + GAP
            c.rect(LAB, row_y, ncols * DX, rh - GAP, "#e9e9e9")
            c.use("screens")
            for (sc, wfig, ih, cap, hfig, path) in figs:
                x0, y0 = colx(sc["col"]) + 6, row_y + 10
                c.rect(x0, y0 + 2, wfig, hfig, "#000000", 6, ' fill-opacity="0.2"')
                c.rect(x0, y0, wfig, hfig, "#ffffff", 6, ' stroke="#bdbdbd" stroke-width="1"')
                if path:
                    ext = os.path.splitext(path)[1].lower()
                    mime = "image/png" if ext == ".png" else "image/jpeg"
                    with open(path, "rb") as fh_:
                        b64 = base64.b64encode(fh_.read()).decode()
                    c.raw('<image x="%s" y="%s" width="%s" height="%s" preserveAspectRatio="none" href="data:%s;base64,%s"/>' % (
                        fmt(x0 + 1), fmt(y0 + 1), fmt(wfig - 2), fmt(ih), mime, b64))
                else:
                    c.rect(x0 + 1, y0 + 1, wfig - 2, ih, "#d9d9d9")
                c.lines(x0 + 9, y0 + 1 + ih + 7 + 12 * 0.97 + 1.5, cap, 12, 600, "#222222", 15.6)
        else:
            cols = {}
            for k, it in enumerate(items):
                cols.setdefault(it["col"], []).append(it)
            maxh = 0.0
            for col, lst in cols.items():
                cur = 12.0
                for k, it in enumerate(lst):
                    s = Sticky(it["kind"], it["text"], col + k, min_h=it.get("min_h", 0), sid=it.get("id"))
                    cur += it.get("dy", 0)
                    s.place(colx(col) + (DX - STK_W) / 2, row_y + cur)
                    cur += s.h + 10
                    drawn.append(s)
                    if it.get("id"):
                        mats[it["id"]] = s
                maxh = max(maxh, cur - 10 + 12)
            rh = max(maxh, 56, rh_min) + GAP
            c.rect(LAB, row_y, ncols * DX, rh - GAP, "#e9e9e9")
        labels.append((row_y, rh - GAP, r["label"]))
        y += rh
    for (ly_, lh_, text) in labels:
        c.use("bg")
        c.rect(0, ly_, LAB - GAP, lh_, "#7b7b7b")
        lines = fonts.wrap(text, 12.5, 400, LAB - GAP - 12)
        y0 = ly_ + lh_ / 2 - (len(lines) - 1) * 8.7 + 4.5
        for i, t in enumerate(lines):
            c.text((LAB - GAP) / 2, y0 + i * 17.2, t, 12.5, 400, "#ffffff", "middle")
    H = int(math.ceil(y + 18))
    c.layers["bg"].insert(bg_idx, '<rect x="0" y="%s" width="%d" height="%s" fill="#f3f3f3"/>' % (fmt(board_top), W, fmt(H - board_top)))

    # ----- связи стикеров и кривая настроения -----
    c.use("arrows")
    for l in doc.get("sticky_links", []):
        a, b = mats.get(l["from"]), mats.get(l["to"])
        if not a or not b:
            continue
        p = (a.x, a.y, a.x + a.w, a.y + a.h, a.cx, a.cy)
        q = (b.x, b.y, b.x + b.w, b.y + b.h, b.cx, b.cy)
        col = "#d33333" if l.get("loss") else "#444444"
        dash = ' stroke-dasharray="6 5"' if l.get("dash") else ""
        if abs(p[4] - q[4]) < 30:
            sx, ex = p[4], q[4]
            sy, ey = (p[3], q[1]) if q[1] > p[3] else (p[1], q[3])
            d = "M%s %s L%s %s" % (fmt(sx), fmt(sy), fmt(ex), fmt(ey))
            pts = [(sx, sy), (ex, ey)]
        elif q[0] > p[2] and abs(q[5] - p[5]) < 400:
            sx, sy, ex, ey = p[2], p[5], q[0], q[5]
            k = max(30, (ex - sx) / 2)
            d = "M%s %s C%s %s,%s %s,%s %s" % (fmt(sx), fmt(sy), fmt(sx + k), fmt(sy), fmt(ex - k), fmt(ey), fmt(ex), fmt(ey))
            pts = [(ex - k, ey), (ex, ey)]
        else:
            sx, sy, ex, ey = p[4], p[3], q[4], q[1]
            k = max(40, (ey - sy) / 2)
            d = "M%s %s C%s %s,%s %s,%s %s" % (fmt(sx), fmt(sy), fmt(sx), fmt(sy + k), fmt(ex), fmt(ey - k), fmt(ex), fmt(ey))
            pts = [(ex, ey - k), (ex, ey)]
        c.raw('<path d="%s" fill="none" stroke="%s" stroke-width="1.6"%s/>' % (d, col, dash))
        c.arrow_head(pts, col, 11.2)
    pts = sorted(((s.cx, s.cy) for s in emotions))
    if len(pts) > 1:
        d = "M%s %s" % (fmt(pts[0][0]), fmt(pts[0][1]))
        for i in range(1, len(pts)):
            mx = (pts[i - 1][0] + pts[i][0]) / 2
            d += " C%s %s,%s %s,%s %s" % (fmt(mx), fmt(pts[i - 1][1]), fmt(mx), fmt(pts[i][1]), fmt(pts[i][0]), fmt(pts[i][1]))
        c.raw('<path d="%s" fill="none" stroke="#8a8a8a" stroke-width="2" stroke-dasharray="2 5" stroke-linecap="round"/>' % d)

    # ----- стикеры -----
    for s_ in drawn:
        s_.draw(c)
    desc = "%s. Версия %s, %s. Источник: %s." % (meta["title"], meta.get("version", ""), meta.get("date", ""), meta.get("source", ""))
    return c.done(W, H, meta["title"], desc)
