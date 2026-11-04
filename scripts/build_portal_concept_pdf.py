#!/usr/bin/env python3
"""Концепт портала (docs/html/portal-concept.html) → поэкранный PDF с привязкой экранов к карте.

Запуск: python3 scripts/build_portal_concept_pdf.py vault/40-reports/<имя>.pdf
"""
import os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reportlab.lib.pagesizes import A4, portrait
from playwright.sync_api import sync_playwright
import build_screens_pdf as B

ROOT = B.ROOT
import glob
_c = glob.glob('/opt/pw-browsers/chromium-*/chrome-linux*/chrome')
if not os.path.exists(B.CHROME) and _c:
    B.CHROME = sorted(_c)[-1]
URL = "file://" + os.path.join(ROOT, "docs/html/portal-concept.html")

def shot(page, tmp, name, full=True):
    page.wait_for_timeout(250)
    p = os.path.join(tmp, name + ".png")
    page.screenshot(path=p, full_page=full)
    if full:
        B.trim(p)
    return p

def capture(tmp):
    pages = []
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path=B.CHROME)
        pg = b.new_page(viewport={"width": 1000, "height": 1300}, device_scale_factor=2)
        pg.goto(URL); pg.wait_for_timeout(300)
        pg.add_style_tag(content="header.top{position:static!important}.cmpbar{position:static!important}.toast{display:none!important}")
        pg.check("#annoSw")
        def go(s): pg.evaluate("__go('%s')" % s)
        def add(img, eb, head, cap): pages.append((img, eb, head, cap))

        add(shot(pg, tmp, "01"), "Этапы 1–3 карты", "Главная страница",
            "Страна, язык и валюта подставлены. Над поиском переключатель направлений. Запрос можно вводить своими словами; примеры — из болей клиентов. Жёлтые отметки показывают узел карты, которому соответствует блок экрана.")
        pg.click("text=Подобрать: вузы"); pg.click("text=Показать подборку"); pg.wait_for_timeout(200)
        add(shot(pg, tmp, "02"), "Этап 3 карты", "Форма направления «Вузы»: недостающее",
            "Портал показывает, что уже известно, и спрашивает только недостающее. Незаполненное обязательное поле подсвечено. Необязательные вопросы свёрнуты. Состав обязательных полей по категориям не утверждён.")
        pg.evaluate("S.d='kp';S.f={};S.showMiss=false;__render()")
        add(shot(pg, tmp, "03"), "Этап 3 карты", "Форма направления «Короткие программы»",
            "У каждого направления свои вопросы: формат, страна при очном обучении, период начала, тема. Условное поле «страна» появляется только при выборе «Очно».")
        pg.evaluate("S.d='vuz';S.f={level:'Бакалавриат',where:'Моя страна',year:'2027',topic:'инженерия'};S.screen='results';__render()")
        pg.click(".fav >> nth=0"); pg.check(".cmp input >> nth=0"); pg.check(".cmp input >> nth=1"); pg.check(".cmp input >> nth=2")
        add(shot(pg, tmp, "04"), "Этап 4 карты", "Выдача «Вузы»: избранное, сравнение, плашка",
            "Карточки с источником и датой, фильтры, сравнение до четырёх. При сравнении трёх вариантов показывается одна плашка (консультация; статус блока под вопросом). Под выдачей — вопрос «Подборка подошла?».")
        pg.evaluate("S.d='pro';S.cmp=[];S.favs=[];S.plashOff={};S.fit=null;__render()")
        add(shot(pg, tmp, "05"), "Этап 4 карты", "Выдача «Профессии»",
            "Спрос, риск автоматизации, навыки; зарплатная вилка подставится из открытых источников с датой. Кнопка «Где учиться» передаёт профессию в подбор вуза. Открытость этих данных против платного модуля Профиля 360 не решена.")
        pg.click(".cardr >> nth=0 >> text=Где учиться"); pg.wait_for_timeout(200)
        add(shot(pg, tmp, "06"), "Этап 5 карты", "Профессия переходит в подбор вуза",
            "Направление переключается, фильтры подставлены. В карточке вуза видно, к каким профессиям он ведёт: из вуза — к профессиям, из профессии — к вузам.")
        pg.evaluate("S.profFilter=null;S.d='vuz';__render()")
        pg.click(".cardr >> nth=0 >> text=Перейти или подать заявку")
        add(shot(pg, tmp, "07", full=False), "Этап 5 карты", "«Большая кнопка»: окно вариантов",
            "Сайт учреждения (оплата за клик), заявка через портал (гипотеза), услуги и пакеты. Набор вариантов не утверждён.")
        pg.click("text=Перейти на сайт учреждения")
        add(shot(pg, tmp, "08", full=False), "Этап 5 карты", "Просьба оставить email",
            "Перед переходом портал просит email: так клиента можно вернуть письмом. Поле необязательное.")
        pg.click("text=Сохранить и перейти")
        add(shot(pg, tmp, "09"), "Этап 5 карты", "Сайт учреждения в новой вкладке",
            "Имитация: клиент изучает программу и подаёт заявку на сайте учреждения, вкладка портала остаётся открытой.")
        pg.click("text=Я вернулся на портал")
        add(shot(pg, tmp, "10"), "Этап 5 карты", "Возврат и статус",
            "Клиент отмечает статус: подал, записался, пока думает. Если не вернулся сам, при заданном email через время приходит письмо.")
        go("services")
        add(shot(pg, tmp, "11"), "Блок 8 карты", "Услуги и пакеты",
            "Состав и условия не определены: вместо цен лист ожидания для проверки спроса. Исполнители — партнёры-провайдеры (гипотеза).")
        go("orient")
        for o in ["Придумывать и рисовать", "Играет в компьютерные игры", "Рисунок и творчество"]:
            pg.click('.opt:has-text("%s")' % o)
        pg.click("text=Показать результат")
        add(shot(pg, tmp, "12"), "Блок 7 карты", "Профориентация без слова в запросе",
            "Бесплатный скрининг, карта рисков выбора, подробный отчёт (цена зависит от канала и страны). Результат подставляется в поиск профессий и в индекс соответствия вузов.")
        go("consult")
        add(shot(pg, tmp, "13"), "Блок 6 карты", "Консультация (статус под вопросом)",
            "Форма-анкета вместо живого звонка: возможная замена по итогам созвона. Решения нет.")
        pg.click("text=Отправить")
        add(shot(pg, tmp, "14"), "Кабинет", "Мой путь",
            "Подборки, избранное, заявки и статусы, напоминания, лист ожидания. Кабинет общий для всех направлений.")
        go("map")
        add(shot(pg, tmp, "15"), "Связь с картой", "Соответствие карте",
            "Таблица: этап карты, узлы схемы, экран концепта, статус решения.")
        b.close()
    return pages

def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "vault/40-reports/2026-11-04-portal-concept.pdf")
    tmp = tempfile.mkdtemp()
    pages = capture(tmp)
    how = ["Каждый экран — снимок интерактивного концепта; жёлтые отметки — узел карты.",
           "Живой концепт: docs/html/portal-concept.html (открывается в браузере, работает без сервера).",
           "Данные на экранах демонстрационные: вузов, цен и сроков здесь нет."]
    B.build_pdf(out, portrait(A4), "Концепт портала Mainexperts\nвузы · колледжи · профессии · короткие программы",
                "Поиск, подборка, сравнение, большая кнопка, возврат и кабинет по единой карте пути (04.11.2026).",
                "Концепт, не утверждён основателем. Карта: docs/html/cjm-poisk-vse-napravleniya.html; описание: docs/26, docs/28.", how, pages)
    print(out)

if __name__ == "__main__":
    main()
