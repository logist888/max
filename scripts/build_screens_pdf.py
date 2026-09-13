#!/usr/bin/env python3
"""Интерактивные HTML-страницы → поэкранный PDF (для тех, кто смотрит с телефона).

Playwright прогоняет страницу по состояниям, снимает каждый экран, ReportLab собирает
PDF в палитре Demo Day: тёмный титул, светлые страницы, золотые акценты, DejaVu Sans.

Запуск:
  python3 scripts/build_screens_pdf.py flows   vault/40-reports/<имя>.pdf
  python3 scripts/build_screens_pdf.py cabinet vault/40-reports/<имя>.pdf
"""
import os, sys, tempfile
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import Paragraph

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
FD = "/usr/share/fonts/truetype/dejavu/"
pdfmetrics.registerFont(TTFont("DV", FD + "DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DV-B", FD + "DejaVuSans-Bold.ttf"))

INK = colors.HexColor("#101010"); LIGHT = colors.HexColor("#f8f8f8")
GOLD = colors.HexColor("#c0a870"); GREY = colors.HexColor("#5f5f5f")
GREY_L = colors.HexColor("#c8c8c8"); LINE = colors.HexColor("#dcdcdc")

# ────────────────────────────── съёмка ──────────────────────────────

def _launch(pw, width, height):
    b = pw.chromium.launch(executable_path=CHROME)
    return b, b.new_page(viewport={"width": width, "height": height}, device_scale_factor=2)


def trim(path):
    """Срезать однотонные поля снизу и справа: полноэкранный снимок добавляет пустоту."""
    from PIL import Image
    im = Image.open(path).convert("RGB")
    w, h = im.size
    bg = im.getpixel((w - 2, h - 2))

    def uniform(box):
        crop = im.crop(box)
        return crop.getcolors(maxcolors=4) and len(crop.getcolors(maxcolors=4)) == 1

    bottom = h
    while bottom > 200 and uniform((0, bottom - 8, w, bottom)):
        bottom -= 8
    right = w
    while right > 400 and uniform((right - 8, 0, right, bottom)):
        right -= 8
    if bottom < h or right < w:
        im.crop((0, 0, min(w, right + 8), min(h, bottom + 8))).save(path)


def _ready(page):
    page.wait_for_timeout(400)
    page.evaluate("document.fonts && document.fonts.ready")
    page.wait_for_timeout(250)


def capture_flows(tmp):
    """Карта путей: сценарий, дорожки и по экрану на каждый шаг обоих путей."""
    from playwright.sync_api import sync_playwright
    url = "file://" + os.path.join(ROOT, "docs/html/partner-flows.html")
    shots = []
    with sync_playwright() as pw:
        b, page = _launch(pw, 1260, 1000)
        page.goto(url); _ready(page)

        def only(sel_list):
            page.evaluate(
                """(keep)=>{['.controls','#calc','.flow','.detail','.foot'].forEach(s=>{
                     var el=document.querySelector(s); if(el) el.style.display = keep.indexOf(s)>=0 ? '' : 'none';});}""",
                sel_list)

        ALL = [".controls", "#calc", ".flow", ".detail", ".foot"]

        def shot(name, keep):
            only(keep)
            p = os.path.join(tmp, name + ".png")
            page.locator("main.wrap").screenshot(path=p)
            shots.append(p)
            return p

        def steps(flow):
            page.click("#tab-" + flow); page.wait_for_timeout(250)
            shot("rail-" + flow, [".flow"])
            out = []
            for i in range(7):
                page.evaluate("(i)=>document.querySelector(\".step[data-i='\"+i+\"']\").click()", i)
                page.wait_for_timeout(200)
                out.append(shot("%s-%d" % (flow, i), [".detail"]))
            return out

        shot("calc-base", [".controls", "#calc"])
        steps("family")
        steps("partner")

        def sel(el_id, val):
            only(ALL)
            page.evaluate("([i,v])=>{var e=document.getElementById(i); e.value=v; e.dispatchEvent(new Event('change'))}",
                          [el_id, val])
            page.wait_for_timeout(200)

        def rng(val):
            only(ALL)
            page.evaluate("(v)=>{var e=document.getElementById('k'); e.value=v; e.dispatchEvent(new Event('input'))}", val)
            page.wait_for_timeout(200)

        sel("tax", "fl")
        shot("calc-fl", [".controls", "#calc"])
        sel("tax", "npd"); sel("kmax", "0"); rng(70000)
        shot("calc-70", [".controls", "#calc"])
        sel("kmax", "50000"); rng(25000); sel("route", "2")
        shot("calc-route2", [".controls", "#calc"])
        b.close()
    return shots


def capture_cabinet(tmp):
    """Кабинет партнёра: двенадцать шагов демонстрации плюс варианты правил."""
    from playwright.sync_api import sync_playwright
    url = "file://" + os.path.join(ROOT, "docs/html/partner-cabinet.html")
    shots = []
    with sync_playwright() as pw:
        b, page = _launch(pw, 900, 640)
        page.goto(url); _ready(page)
        page.add_style_tag(content=".demobar{display:none!important}body{padding-bottom:16px}"
                                   ".rail{flex-wrap:wrap!important;overflow:visible!important}")

        def shot(name):
            page.wait_for_timeout(250)
            p = os.path.join(tmp, name + ".png")
            page.screenshot(path=p, full_page=True)
            trim(p)
            shots.append(p)

        def nxt(n=1):
            for _ in range(n):
                page.evaluate("document.getElementById('next').click()")
                page.wait_for_timeout(200)

        def section(sid):
            page.evaluate("(s)=>{document.querySelector('[data-act=sec][data-v='+JSON.stringify(s)+']').click()}", sid)
            page.wait_for_timeout(200)

        shot("01-vhod")                                   # шаг 0
        page.click("[data-act=login]"); nxt(0); shot("02-oferta-do")
        page.click("#terms"); shot("03-oferta-prinyata")
        nxt(); shot("04-status")                          # шаг 2
        page.select_option("#tax", "none"); shot("05-status-net")
        page.select_option("#tax", "person")
        nxt(); shot("06-usloviya")                        # шаг 3
        nxt(); shot("07-cena")                            # шаг 4
        page.eval_on_selector("#k", "el=>{el.value=19000; el.dispatchEvent(new Event('input'))}")
        shot("08-cena-nizhe")
        page.eval_on_selector("#k", "el=>{el.value=42000; el.dispatchEvent(new Event('input'))}")
        shot("09-cena-vyshe")
        page.eval_on_selector("#k", "el=>{el.value=28000; el.dispatchEvent(new Event('input'))}")
        nxt(); shot("10-predlozheniya")                   # шаг 5
        nxt(); shot("11-stranica-semi")                   # шаг 6
        page.click("[data-act=direct]"); shot("12-stranica-zacherknuto")
        page.click("[data-act=direct]")
        page.click("[data-act=second]"); shot("13-dva-predlozheniya")
        page.click("[data-act=second]")
        nxt(); shot("14-oplaty")                          # шаг 7
        nxt(); shot("15-uderzhanie")                      # шаг 8
        nxt(); shot("16-vyplata")                         # шаг 9
        nxt(); shot("17-vozvrat-dolg")                    # шаг 10
        nxt(); shot("18-panel")                           # шаг 11
        section("kit"); shot("19-materialy")
        section("alerts"); shot("20-uvedomleniya")
        section("help"); shot("21-pomoshch")
        b.close()
    return shots

# ────────────────────────────── сборка PDF ──────────────────────────────

def _para(text, size, color, leading=None, bold=False):
    return Paragraph(text, ParagraphStyle("p", fontName="DV-B" if bold else "DV", fontSize=size,
                                          leading=leading or size * 1.35, textColor=color))


def build_pdf(out, page_size, title, lead, meta, how, pages):
    c = rl_canvas.Canvas(out, pagesize=page_size)
    PW, PH = page_size
    ML = MR = 34; MT = 38; MB = 30
    W = PW - ML - MR

    # титул
    c.setFillColor(INK); c.rect(0, 0, PW, PH, stroke=0, fill=1)
    c.setFillColor(GOLD); c.rect(ML, PH - MT - 4, 54, 3, stroke=0, fill=1)
    y = PH - MT - 30
    c.setFont("DV-B", 26); c.setFillColor(colors.white)
    for line in title.split("\n"):
        c.drawString(ML, y, line); y -= 32
    y -= 6
    p = _para(lead, 11, GREY_L, 15.5); w, h = p.wrap(min(W, 520), PH); p.drawOn(c, ML, y - h); y -= h + 26
    c.setFont("DV-B", 9); c.setFillColor(GOLD); c.drawString(ML, y, "КАК ЧИТАТЬ"); y -= 16
    for item in how:
        p = _para("— " + item, 10, GREY_L, 14); w, h = p.wrap(min(W, 560), PH); p.drawOn(c, ML, y - h); y -= h + 6
    p = _para(meta, 8.5, GREY, 12); w, h = p.wrap(min(W, 600), PH); p.drawOn(c, ML, MB + 6)
    c.showPage()

    total = len(pages)
    for i, (img, eyebrow, head, caption) in enumerate(pages, 1):
        c.setFillColor(LIGHT); c.rect(0, 0, PW, PH, stroke=0, fill=1)
        y = PH - MT
        c.setFont("DV-B", 8); c.setFillColor(GOLD)
        c.drawString(ML, y, ("ЭКРАН %d ИЗ %d · " % (i, total)) + eyebrow.upper())
        y -= 18
        c.setFont("DV-B", 14); c.setFillColor(INK); c.drawString(ML, y, head); y -= 14
        p = _para(caption, 9, GREY, 12.5); w, h = p.wrap(W, PH); p.drawOn(c, ML, y - h); y -= h + 12

        box_h = y - MB - 14
        iw, ih = ImageReader(img).getSize()
        sc = min(W / iw, box_h / ih)
        dw, dh = iw * sc, ih * sc
        x = ML + (W - dw) / 2
        c.setFillColor(colors.white); c.setStrokeColor(LINE); c.setLineWidth(0.6)
        c.rect(x - 4, y - dh - 4, dw + 8, dh + 8, stroke=1, fill=1)
        c.drawImage(img, x, y - dh, width=dw, height=dh, mask="auto")

        c.setStrokeColor(GOLD); c.setLineWidth(0.7); c.line(ML, MB + 12, PW - MR, MB + 12)
        c.setFont("DV", 7.5); c.setFillColor(GREY)
        c.drawString(ML, MB + 2, "MAINEXPERTS · партнёрская сеть · демонстрационные данные")
        c.drawRightString(PW - MR, MB + 2, "%d" % i)
        c.showPage()
    c.save()


FLOWS_PAGES = [
    ("Сценарий и расчёт", "Калькулятор сделки",
     "Цена партнёра, верхняя граница, маршрут денег и налоговый режим. Ниже — что получает семья, партнёр и платформа при этих значениях."),
    ("Путь семьи", "Семь этапов семьи: дорожки",
     "Строки дорожек: что происходит с семьёй, что делает партнёр, что фиксирует платформа."),
    ("Путь семьи · этап 1", "Повод",
     "Родитель не ищет услугу, повод создаёт разговор с партнёром. Точка отказа и реплики трёх семей."),
    ("Путь семьи · этап 2", "Переход по ссылке",
     "Имя партнёра на странице, цена совпадает с обещанной. Остановленное предложение показывает завершение, а не подмену цены."),
    ("Путь семьи · этап 3", "Цена и состав",
     "Состав и срок одинаковы при любой цене. Зачёркнутая цена сайта — только если платформа продаёт по ней в тот же период."),
    ("Путь семьи · этап 4", "Оформление и оплата",
     "Заказ создаётся до платежа со снимком цены. Повторное уведомление шлюза не создаёт второго доступа и второго начисления."),
    ("Путь семьи · этап 5", "Доступ и прохождение",
     "Доступ и письмо сразу после подтверждения платежа. Незавершённое прохождение — напоминание."),
    ("Путь семьи · этап 6", "Результат и возврат",
     "Отчёт, раздел «как читать», обращение о возврате. Рассмотрение возврата отделено от расчёта с партнёром."),
    ("Путь семьи · этап 7", "Повтор",
     "Семья возвращается за следующим шагом или приводит знакомых. Старые заказы не меняются от новых цен."),
    ("Путь партнёра", "Семь шагов партнёра: дорожки",
     "От знакомства с условиями до выплаты и повторной продажи."),
    ("Путь партнёра · шаг 1", "Знакомство",
     "Страница партнёра, условия, образец отчёта, экономика примерами. Проверка: партнёр называет три цены и своё начисление."),
    ("Путь партнёра · шаг 2", "Подключение",
     "Регистрация и оферта без экзамена. Статус для выплат заполняется позже и кабинет не блокирует."),
    ("Путь партнёра · шаг 3", "Цена предложения",
     "Шкала от минимальной цены до верхней границы, мгновенный расчёт начисления. Проверка цены — на сервере."),
    ("Путь партнёра · шаг 4", "Инструмент",
     "Ссылка, код, предпросмотр страницы семьи, материалы. Цена созданного предложения не редактируется."),
    ("Путь партнёра · шаг 5", "Семья",
     "Переходы, обращения и оплаты раздельно. Данных ребёнка и чужих сделок в кабинете нет."),
    ("Путь партнёра · шаг 6", "Расчёт и выплата",
     "Удержание, доступность, реестр выплат, ветки по налоговому статусу, отказ банка и долг."),
    ("Путь партнёра · шаг 7", "Повтор и панель",
     "Повторная активность как отдельный признак. Панель пилота без процентов на малых числах."),
    ("Варианты расчёта", "Партнёр — физическое лицо",
     "Взносы сверх начисления ложатся на платформу, поэтому её результат падает сильнее, чем на других режимах."),
    ("Варианты расчёта", "Граница снята, цена 70 000",
     "Без верхней границы цена уходит выше публичной цены сайта: сравнение не показывается, включается внутренний сигнал."),
    ("Варианты расчёта", "Маршрут 2",
     "Партнёр платит платформе сам и продаёт семье от своего имени. Выключен до заключения юриста."),
]

CABINET_PAGES = [
    ("Вход", "Вход по приглашению",
     "Партнёр входит по ссылке координатора. Регистрация с улицы на пилоте закрыта, партнёры — резиденты России."),
    ("Подключение", "Оферта не принята",
     "Кабинет открыт, но создать предложение нельзя. Условия, материалы и расчёт доступны для чтения."),
    ("Подключение", "Оферта принята",
     "Сохраняются версия условий, дата и время. Экзамена, обучения и предоплаты нет."),
    ("Статус и реквизиты", "Статус для выплат",
     "Физическое лицо: платформа удерживает налог на доходы 13 процентов. Взносы к начислению не прибавляются и из него не вычитаются."),
    ("Статус и реквизиты", "Статус не указан",
     "Кабинет работает, выплата заблокирована с пояснением. Значения «нерезидент» и «юридическое лицо» на пилоте недоступны."),
    ("Условия", "Три цены словами",
     "Сумма платформы, минимальная и рекомендованная цена, верхняя граница. Ни одной буквы: только слова и суммы."),
    ("Новое предложение", "Цена и расчёт",
     "Шкала с отметками минимума, рекомендованной цены и границы. Расчёт пересчитывается на лету."),
    ("Новое предложение", "Цена ниже минимальной",
     "Сервер отклонит такое предложение и назовёт допустимый диапазон. Кнопка создания недоступна."),
    ("Новое предложение", "Дороже рекомендованной",
     "Это не ошибка: предложение создаётся. Цену семье объясняет партнёр."),
    ("Предложения", "Ссылка и код",
     "Одно предложение, ссылка и код ведут на одну страницу. Цена зафиксирована: изменить её можно только новым предложением."),
    ("Предложения", "Страница семьи",
     "Предпросмотр того, что видит семья: имя партнёра, цена, состав, раскрытие продавца. Реквизиты подставляет платформа."),
    ("Предложения", "Зачёркнутая цена сайта",
     "Появляется только при включённой прямой продаже платформы по цене сайта в тот же период."),
    ("Предложения", "Два предложения с разной ценой",
     "Предупреждение о расхождении цен для одной аудитории. Заказы, оформленные раньше, сохраняют свою цену."),
    ("Обращения и оплаты", "Первая оплата",
     "Переходы, обращения и оплаты считаются раздельно. Ни одного поля с данными ребёнка."),
    ("Начисления", "Начисление и удержание",
     "Сумма доступна через 14 дней после оплаты или через 7 дней после выдачи отчёта — что наступит позже, но не дольше 60 дней."),
    ("Начисления", "Выплата",
     "Начислено до налогов и к выплате показаны раздельно, разница объясняется текстом. День реестра — вторник."),
    ("Начисления", "Возврат после выплаты",
     "Выплаченное назад не требуют: возникает долг, он зачитывается против следующего начисления."),
    ("Панель", "Панель пилота",
     "Доли и конверсии не показываются, пока наблюдений меньше десяти. Покупки из круга основателя — отдельной строкой."),
    ("Материалы", "Готовые материалы",
     "Образец отчёта и тексты с подставленной ценой. Названия методик не используются, обещать поступление нельзя."),
    ("Уведомления", "Уведомления партнёру",
     "Оплата, выдача отчёта, доступность суммы, выплата, возврат. Имени семьи в уведомлениях нет."),
    ("Помощь", "Обращение в поддержку",
     "Вопрос привязывается к заказу или предложению. Данные ребёнка координатору в этой форме не передаются."),
]


def main():
    which, out = sys.argv[1], sys.argv[2]
    out = out if os.path.isabs(out) else os.path.join(ROOT, out)
    tmp = tempfile.mkdtemp(prefix="screens-")
    if which == "flows":
        shots = capture_flows(tmp)
        pages = [(s,) + m for s, m in zip(shots, FLOWS_PAGES)]
        build_pdf(out, landscape(A4), "Пути семьи и партнёра\nэкран за экраном",
                  "Снимки интерактивной карты путей: каждый шаг обоих путей и варианты расчёта. "
                  "Версия для чтения там, где интерактивная страница не открывается.",
                  "Источник: docs/15-partner-network-tz.md, docs/16-partner-flows-tz.md. Значения для России — "
                  "рабочие значения пилота от 09.09.2026, не решения. Снимки сделаны 13.09.2026. "
                  "Ставки налога с оборота 6 % и эквайринга 2,5 % — параметры; правовые пункты — вопросы к юристу.",
                  ["Сначала расчёт: он задаёт цифры, которые дальше встречаются на шагах.",
                   "Затем путь семьи: семь этапов от повода до повтора.",
                   "Затем путь партнёра: семь шагов от знакомства до выплаты.",
                   "В конце — три варианта расчёта, меняющие исход сделки."],
                  pages)
    else:
        shots = capture_cabinet(tmp)
        pages = [(s,) + m for s, m in zip(shots, CABINET_PAGES)]
        build_pdf(out, portrait(A4), "Кабинет партнёра\nэкран за экраном",
                  "Снимки кликабельного прототипа кабинета: двенадцать шагов демонстрации и состояния правил, "
                  "которые в прототипе проверяются нажатием. Версия для чтения с телефона.",
                  "Источник: docs/16-partner-flows-tz.md (пути П1–П7), docs/15-partner-network-tz.md (экраны ИНТ-01…ИНТ-15). "
                  "Заказы, суммы и даты вымышленные — реальных продаж и платежей нет. Снимки сделаны 13.09.2026. "
                  "Цены — рабочие значения пилота; верхняя граница 50 000 — умолчание до решения основателя.",
                  ["Порядок экранов повторяет демонстрацию: вход, оферта, цена, ссылка, оплаты, деньги, панель.",
                   "Экраны с пометкой о правиле показывают, что именно запрещает или предупреждает система.",
                   "Нижняя панель с кнопками «Назад» и «Далее» на снимках скрыта: её роль выполняет порядок страниц.",
                   "Разделы «Материалы», «Уведомления» и «Помощь» доступны в кабинете из бокового меню."],
                  pages)
    print(out)


if __name__ == "__main__":
    main()
