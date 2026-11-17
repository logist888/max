# -*- coding: utf-8 -*-
"""Чтение journey.yaml и проверка до отрисовки. Ошибки называют файл, строку, путь к полю."""
import os

import yaml

SHAPES = ("term", "proc", "dec", "data", "doc", "db", "manual", "pre", "note")
STICKY_KINDS = ("y", "b", "r", "g", "o", "w", "gr", "ghost", "ey")
ROW_TYPES = ("stack", "goal", "emotion", "screens")
MAX_NODE_TEXT = 260
MAX_STICKY_TEXT = 320
MAX_COLS = 400


class ValidationError(Exception):
    def __init__(self, problems):
        super().__init__("\n".join(problems))
        self.problems = problems


class LMap(dict):
    line = 0


class LList(list):
    line = 0


class _Loader(yaml.SafeLoader):
    pass


def _map(loader, node):
    loader.flatten_mapping(node)
    d = LMap()
    d.line = node.start_mark.line + 1
    for k, v in node.value:
        d[loader.construct_object(k, deep=True)] = loader.construct_object(v, deep=True)
    return d


def _seq(loader, node):
    s = LList()
    s.line = node.start_mark.line + 1
    s.extend(loader.construct_object(v, deep=True) for v in node.value)
    return s


_Loader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _map)
_Loader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_SEQUENCE_TAG, _seq)


def _line(o, default=0):
    return getattr(o, "line", default)


class Checker:
    def __init__(self, path):
        self.path = os.path.basename(path)
        self.problems = []
        self.warnings = []

    def err(self, obj, where, msg):
        self.problems.append("%s:%s: %s: %s" % (self.path, _line(obj) or "?", where, msg))

    def warn(self, obj, where, msg):
        self.warnings.append("%s:%s: %s: %s" % (self.path, _line(obj) or "?", where, msg))


def _need(ck, obj, where, key, types=(str,), nonempty=True):
    if not isinstance(obj, dict):
        ck.err(obj, where, "ожидался словарь «ключ: значение»")
        return None
    v = obj.get(key)
    if v is None:
        ck.err(obj, where, "нет обязательного поля «%s»" % key)
        return None
    if isinstance(v, bool) or not isinstance(v, types):
        ck.err(obj, where, "поле «%s»: ожидался тип %s, получено %r" % (key, "/".join(t.__name__ for t in types), v))
        return None
    if nonempty and isinstance(v, str) and not v.strip():
        ck.err(obj, where, "поле «%s» пустое" % key)
        return None
    return v


def load(path):
    with open(path, encoding="utf-8") as fh:
        try:
            doc = yaml.load(fh, Loader=_Loader)
        except yaml.YAMLError as e:
            mark = getattr(e, "problem_mark", None)
            raise ValidationError(["%s:%s: синтаксис YAML: %s" % (os.path.basename(path), (mark.line + 1) if mark else "?", getattr(e, "problem", e))])
    if not isinstance(doc, dict):
        raise ValidationError(["%s: файл пуст или это не словарь верхнего уровня" % os.path.basename(path)])
    ck = Checker(path)
    base = os.path.dirname(os.path.abspath(path))
    validate(doc, ck, base)
    if ck.problems:
        raise ValidationError(ck.problems)
    doc["_warnings"] = ck.warnings
    doc["_base"] = base
    normalize(doc)
    return doc


def validate(doc, ck, base):
    known = {"meta", "header", "lanes", "stages", "flow", "rows", "stickies", "sticky_links", "screens"}
    for k in doc:
        if k not in known:
            ck.err(doc, "верхний уровень", "неизвестный раздел «%s» (допустимы: %s)" % (k, ", ".join(sorted(known))))
    meta = doc.get("meta")
    if _need(ck, doc, "верхний уровень", "meta", (dict,)) is not None:
        _need(ck, meta, "meta", "title")
    # дорожки
    lane_ids = {}
    lanes = _need(ck, doc, "верхний уровень", "lanes", (list,))
    for i, ln in enumerate(lanes or []):
        w = "lanes[%d]" % i
        lid = _need(ck, ln, w, "id")
        _need(ck, ln, w, "label")
        st = ln.get("style") if isinstance(ln, dict) else None
        if st is not None and (isinstance(st, bool) or not isinstance(st, int) or not 0 <= st <= 6):
            ck.err(ln, w, "style должен быть числом 0–6 (цветовая схема дорожки)")
        if lid:
            if lid in lane_ids:
                ck.err(ln, w, "дорожка «%s» уже объявлена" % lid)
            lane_ids[lid] = i
    if lanes is not None and not lanes:
        ck.err(lanes, "lanes", "нужна хотя бы одна дорожка")
    # узлы
    flow = _need(ck, doc, "верхний уровень", "flow", (dict,))
    node_ids = {}
    ncols = 0
    if flow is not None:
        lh = flow.get("lane_height")
        if lh is not None and (isinstance(lh, bool) or not isinstance(lh, (int, float)) or not 120 <= lh <= 600):
            ck.err(flow, "flow", "lane_height: число от 120 до 600")
        nodes = _need(ck, flow, "flow", "nodes", (list,))
        for i, n in enumerate(nodes or []):
            w = "flow.nodes[%d]" % i
            nid = _need(ck, n, w, "id")
            if nid:
                w = "flow.nodes[%d] (id=%s)" % (i, nid)
                if nid in node_ids:
                    ck.err(n, w, "шаг с таким id уже есть (строка %s)" % node_ids[nid])
                node_ids[nid] = _line(n)
            shape = _need(ck, n, w, "shape")
            if shape and shape not in SHAPES:
                ck.err(n, w, "неизвестная форма «%s» (допустимы: %s)" % (shape, ", ".join(SHAPES)))
            col = _need(ck, n, w, "col", (int,))
            if col is not None:
                if not 0 <= col < MAX_COLS:
                    ck.err(n, w, "col вне диапазона 0–%d" % (MAX_COLS - 1))
                else:
                    ncols = max(ncols, col + 1)
            lane = _need(ck, n, w, "lane")
            if lane and lane not in lane_ids:
                ck.err(n, w, "неизвестная дорожка «%s» (есть: %s)" % (lane, ", ".join(lane_ids) or "ни одной"))
            text = _need(ck, n, w, "text")
            if text and len(text) > MAX_NODE_TEXT:
                ck.err(n, w, "текст шага слишком длинный: %d знаков при пределе %d; сократите или разбейте на два шага" % (len(text), MAX_NODE_TEXT))
            if n.get("style") is not None and n["style"] not in lane_ids:
                ck.err(n, w, "style: неизвестная дорожка «%s»" % n["style"])
        edges = flow.get("edges", [])
        if not isinstance(edges, list):
            ck.err(flow, "flow", "edges должен быть списком")
            edges = []
        for i, e in enumerate(edges):
            w = "flow.edges[%d]" % i
            a = _need(ck, e, w, "from")
            b = _need(ck, e, w, "to")
            if a and a not in node_ids:
                ck.err(e, w, "связь идёт от несуществующего шага «%s»" % a)
            if b and b not in node_ids:
                ck.err(e, w, "связь идёт к несуществующему шагу «%s»" % b)
            if a and b and a == b:
                ck.err(e, w, "связь ведёт шаг сам в себя")
            p = e.get("ports") if isinstance(e, dict) else None
            if p is not None and not (isinstance(p, str) and len(p) == 2 and all(c in "lrtb" for c in p)):
                ck.err(e, w, "ports: две буквы из l, r, t, b (откуда и куда), например «rl»")
            if isinstance(e, dict) and e.get("label_at") not in (None, "start", "mid"):
                ck.err(e, w, "label_at: start или mid")
            c = e.get("corridor") if isinstance(e, dict) else None
            if c is not None:
                if not isinstance(c, dict) or c.get("lane") not in lane_ids or not isinstance(c.get("dy"), (int, float)):
                    ck.err(e, w, "corridor: {lane: <id дорожки>, dy: <число>}")
    # этапы
    stage_ids = {}
    stages = _need(ck, doc, "верхний уровень", "stages", (list,))
    spans = []
    for i, s in enumerate(stages or []):
        w = "stages[%d]" % i
        sid = _need(ck, s, w, "id")
        _need(ck, s, w, "label")
        a = _need(ck, s, w, "from", (int,))
        b = _need(ck, s, w, "to", (int,))
        if sid:
            w = "stages[%d] (id=%s)" % (i, sid)
            if sid in stage_ids:
                ck.err(s, w, "этап с таким id уже есть")
            stage_ids[sid] = True
        if a is not None and b is not None:
            if a < 0 or b < a or b >= MAX_COLS:
                ck.err(s, w, "from/to: 0 ≤ from ≤ to < %d" % MAX_COLS)
            else:
                ncols = max(ncols, b + 1)
                for (x0, x1, o) in spans:
                    if a <= x1 and x0 <= b:
                        ck.err(s, w, "этап пересекается с этапом на строке %s по колонкам" % _line(o))
                spans.append((a, b, s))
        col = s.get("color") if isinstance(s, dict) else None
        if col is not None and col not in ("cyan", "blue") and not (isinstance(col, str) and col.startswith("#") and len(col) in (4, 7)):
            ck.err(s, w, "color: cyan, blue или #rrggbb")
    # ряды
    row_ids = {}
    rows = _need(ck, doc, "верхний уровень", "rows", (list,))
    for i, r in enumerate(rows or []):
        w = "rows[%d]" % i
        rid = _need(ck, r, w, "id")
        _need(ck, r, w, "label")
        t = r.get("type", "stack") if isinstance(r, dict) else None
        if t not in ROW_TYPES:
            ck.err(r, w, "type: один из %s" % ", ".join(ROW_TYPES))
        if rid:
            if rid in row_ids:
                ck.err(r, w, "ряд «%s» уже объявлен" % rid)
            row_ids[rid] = t
    # стикеры
    sticky_ids = {}
    stickies = doc.get("stickies", [])
    if not isinstance(stickies, list):
        ck.err(doc, "stickies", "ожидался список")
        stickies = []
    for i, s in enumerate(stickies):
        w = "stickies[%d]" % i
        row = _need(ck, s, w, "row")
        sid = s.get("id") if isinstance(s, dict) else None
        if sid:
            w += " (id=%s)" % sid
            if sid in sticky_ids:
                ck.err(s, w, "стикер с таким id уже есть (строка %s)" % sticky_ids[sid])
            sticky_ids[sid] = _line(s)
        text = _need(ck, s, w, "text")
        if text and len(text) > MAX_STICKY_TEXT:
            ck.err(s, w, "текст стикера слишком длинный: %d знаков при пределе %d" % (len(text), MAX_STICKY_TEXT))
        kind = _need(ck, s, w, "kind")
        if kind and kind not in STICKY_KINDS:
            ck.err(s, w, "неизвестный цвет «%s» (допустимы: %s)" % (kind, ", ".join(STICKY_KINDS)))
        if row is None:
            continue
        if row not in row_ids:
            ck.err(s, w, "неизвестный ряд «%s» (есть: %s)" % (row, ", ".join(row_ids) or "ни одного"))
            continue
        t = row_ids[row]
        if t == "goal":
            st = _need(ck, s, w, "stage")
            if st and st not in stage_ids:
                ck.err(s, w, "неизвестный этап «%s»" % st)
        elif t == "screens":
            ck.err(s, w, "в ряд типа screens стикеры не кладут: используйте раздел screens")
        else:
            col = _need(ck, s, w, "col", (int,))
            if col is not None:
                if not 0 <= col < MAX_COLS:
                    ck.err(s, w, "col вне диапазона")
                else:
                    ncols = max(ncols, col + 1)
        if t == "emotion" and s.get("level") not in (-1, 0, 1):
            ck.err(s, w, "для эмоции нужно поле level: 1 (радость), 0 (нейтрально) или -1 (боль)")
        for k in ("dy", "min_h"):
            if s.get(k) is not None and (isinstance(s[k], bool) or not isinstance(s[k], (int, float))):
                ck.err(s, w, "%s: ожидалось число" % k)
    # связи стикеров
    links = doc.get("sticky_links", [])
    if not isinstance(links, list):
        ck.err(doc, "sticky_links", "ожидался список")
        links = []
    for i, l in enumerate(links):
        w = "sticky_links[%d]" % i
        a = _need(ck, l, w, "from")
        b = _need(ck, l, w, "to")
        for v, nm in ((a, "from"), (b, "to")):
            if v and v not in sticky_ids:
                ck.err(l, w, "%s: стикера с id «%s» нет" % (nm, v))
    # экраны
    scr = doc.get("screens", [])
    if not isinstance(scr, list):
        ck.err(doc, "screens", "ожидался список")
        scr = []
    for i, s in enumerate(scr):
        w = "screens[%d]" % i
        col = _need(ck, s, w, "col", (int,))
        if col is not None:
            ncols = max(ncols, col + 1)
        span = s.get("span", 2) if isinstance(s, dict) else 2
        if isinstance(span, bool) or not isinstance(span, int) or span < 1:
            ck.err(s, w, "span: целое число колонок ≥ 1")
        _need(ck, s, w, "caption")
        img = _need(ck, s, w, "image")
        if img and not os.path.exists(os.path.join(base, img)):
            ck.warn(s, w, "файла снимка «%s» нет: вместо него будет серая рамка" % img)
    if scr and not any(t == "screens" for t in row_ids.values()):
        ck.err(doc, "screens", "есть снимки, но нет ряда с type: screens")
    if ncols == 0 and not ck.problems:
        ck.err(doc, "верхний уровень", "карта пуста: ни одного шага и стикера")
    doc["_ncols"] = ncols


def normalize(doc):
    doc.setdefault("header", {})
    for i, ln in enumerate(doc["lanes"]):
        ln.setdefault("style", i % 7)
    for s in doc["stages"]:
        s.setdefault("board_label", s["label"])
        s.setdefault("color", "cyan")
