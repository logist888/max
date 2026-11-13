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
URL = "file://" + os.path.join(ROOT, "docs/html/portal-concept.html") + "?demo=1"
URL_FIRST = "file://" + os.path.join(ROOT, "docs/html/portal-concept.html")

def shot(page, tmp, name, full=True):
    page.wait_for_timeout(250)
    p = os.path.join(tmp, name + ".jpg")
    page.screenshot(path=p, full_page=full, type="jpeg", quality=72)
    if full:
        B.trim(p)
    return p

def capture(tmp):
    pages = []
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path=B.CHROME)
        pg = b.new_page(viewport={"width": 1100, "height": 1300}, device_scale_factor=1.5)
        # первый вход: заставка и cookies (без параметров, чистый браузер)
        ctx2 = b.new_context(viewport={"width": 1100, "height": 760}, device_scale_factor=1.5)
        p2 = ctx2.new_page(); p2.goto(URL_FIRST); p2.wait_for_timeout(700)
        def add0(img, eb, head, cap): pages.append((img, eb, head, cap))
        add0(shot(p2, tmp, "00a", full=False), "Первый вход", "Заставка: кольцо вокруг логотипа",
            "При первой загрузке 1–2 секунды вращается кольцо вокруг логотипа на тёмном фоне, затем заставка гаснет. Логотип — «Золотые горы».")
        p2.wait_for_timeout(2800)
        add0(shot(p2, tmp, "00b", full=False), "Первый вход", "Баннер cookies внизу страницы",
            "Стандартный баннер: «Принять все», «Только необходимые», «Настроить» (окно с переключателями необходимых, аналитических и маркетинговых cookies). Решение запоминается в браузере.")
        ctx2.close()
        pg.goto(URL); pg.wait_for_timeout(300)
        pg.add_style_tag(content="header.top{position:static!important}.cmpbar{position:static!important}.toast{display:none!important}")
        pg.check("#annoSw")
        pg.evaluate("S.noAnim=true;S.tabPinned=false")
        ev = pg.evaluate
        def add(img, eb, head, cap): pages.append((img, eb, head, cap))
        def state(country, d="vuz", screen="home", extra=""):
            ev("setCountry(%r);S.d=%r;S.f={};S.cmp=[];S.favs=[];S.plashOff={};S.fit=null;S.profFilter=null;S.quizProf=null;S.quiz=false;S.sort='best';S.cal=null;S.showMiss=false;S.lang=null;S.langManual=false;S.cur=null;S.curManual=false;S.user=null;%s;S.screen=%r;__render();window.scrollTo(0,0)" % (country, d, extra, screen))
        VUZ = "S.f={level:'Бакалавриат',where:'Моя страна',year:'2027',topic:'Инженерия'}"

        state("Россия")
        add(shot(pg, tmp, "01"), "Этапы 1–3 карты", "Главная: слоган, поиск, баннер, статьи, вопросы, подвал",
            "Слоган «Поиск и подбор» с печатающимся типом поиска. Вкладки направлений и строка условий. Ниже сменяющийся баннер («Не знаете, с чего начать? Мы рекомендуем бесплатный тест», профориентация, слежение, короткие программы на лето), «Советы и тренды» (статьи-заглушки), вопросы и ответы и подвал с настройками региона, документами и странами. Жёлтые отметки показывают узел карты.")
        state("Казахстан")
        add(shot(pg, tmp, "02"), "Этап 2 карты", "Страна Казахстан: язык и валюта подставлены сразу",
            "При выборе страны интерфейс сразу переходит на её язык (казахский), цены пересчитываются в тенге. Язык можно сменить отдельно.")
        ev("openRegion()"); pg.wait_for_timeout(200)
        add(shot(pg, tmp, "02b", full=False), "Этап 2 карты", "Региональные настройки: язык, страна и валюта в одном окне",
            "Одна кнопка в шапке («Русский · Россия · ₽ RUB») открывает окно с тремя списками: язык, страна или регион, валюта. Ссылка «Switch to English» переключает на английский. Выбор страны подставляет её язык и валюту, которые можно изменить отдельно. Решение по образцу Skyscanner.")
        ev("closeModal()")
        state("Казахстан", screen="results", extra="S.f={level:'Бакалавриат',where:'Моя страна',year:'2027',topic:'Инженерия'};S.lang='en';S.langManual=true")
        add(shot(pg, tmp, "02c"), "Этап 4 карты", "Английский язык при выборе страны Казахстан",
            "Язык интерфейса выбран вручную и сохраняется при смене страны; цены остаются в тенге.")
        state("Россия", extra="S.showMiss=true")
        add(shot(pg, tmp, "03", full=False), "Этап 3 карты", "Недостающее подсвечено в строке поиска",
            "Если не хватает обязательного поля, оно подсвечено в той же строке. Незаполненное не блокирует поиск целиком: портал спрашивает только то, чего нет.")
        state("Россия", screen="results", extra=VUZ + ";S.favs=['v1'];S.cmp=['v1','v2','v3']")
        add(shot(pg, tmp, "04"), "Этап 4 карты", "Выдача «Вузы»: цены в рублях, изображения, сравнение",
            "Календарь цен по годам поступления, сортировка, фильтр по цене. В карточке: изображение, шансы по баллам, срок подачи, цена за год и за весь срок. При сравнении трёх вариантов появляется одна плашка. Под выдачей вопрос «Подборка подошла?» с пояснением, что ответ делает результаты точнее.")
        state("Россия", screen="results", extra=VUZ)
        ev("fit('yes')"); pg.wait_for_timeout(200)
        add(shot(pg, tmp, "04b", full=False), "Момент 1: аккаунт", "После ответа «Подборка подошла?»",
            "Если клиент ответил на вопрос внизу выдачи, предлагаем создать аккаунт, чтобы сохранять результаты. Окно по образцу Skyscanner: одно поле email, вход через Google, Apple, Facebook, крестик.")
        ev("closeModal();S.user=null;S.favs=[];__render();toggleFav('v1')"); pg.wait_for_timeout(200)
        add(shot(pg, tmp, "04c", full=False), "Момент 2: аккаунт", "Сердечко у карточки, «Сохранить», «Поделиться»",
            "Любое действие сохранения без аккаунта открывает то же окно. После создания аккаунта действие выполняется.")
        ev("closeModal();S.user=null;S.favs=[];__render();big('v1')"); pg.wait_for_timeout(100)
        ev("closeModal();goSite()"); pg.wait_for_timeout(200)
        add(shot(pg, tmp, "04d", full=False), "Момент 3: аккаунт", "Перед переходом на сайт учреждения",
            "«Большая кнопка» → «Перейти на сайт»: просим email, чтобы вернуть клиента письмом. Можно пропустить и перейти без аккаунта.")
        ev("closeModal();S.user=null;S.screen='orient';S.quizA={0:'Придумывать и рисовать',1:'Играет в компьютерные игры',2:'Рисунок и творчество'};__render();needAuth('quiz',()=>{S.quizDone=true;__render()},['Показать без сохранения',()=>{}])"); pg.wait_for_timeout(200)
        add(shot(pg, tmp, "04e", full=False), "Момент 4: аккаунт", "Результат разбора ребёнка",
            "Результат бесплатного разбора сохраняется в аккаунте; можно показать без сохранения.")
        ev("closeModal();S.user=null;S.quizDone=false")
        state("Казахстан", screen="results", extra=VUZ + ";S.favs=['v1']")
        add(shot(pg, tmp, "05"), "Этап 4 карты", "Выдача на казахском, цены в тенге",
            "Тот же экран для Казахстана: язык интерфейса, названия, даты и валюта.")
        state("ОАЭ", screen="results", extra=VUZ)
        add(shot(pg, tmp, "06"), "Этап 4 карты", "Выдача на арабском (справа налево), цены в дирхамах",
            "Для арабского языка направление письма и компоновка зеркальные.")
        state("Россия", d="kp", screen="results", extra="S.f={format:'Онлайн',period:'Укажу даты',dateFrom:'2027-07-01',dateTo:'2027-07-31',topic:'Программирование'}")
        add(shot(pg, tmp, "06b"), "Этап 3–4 карты", "Короткие программы: даты начала и окончания",
            "При выборе «Укажу даты» в строке поиска появляются поля «Дата начала» и «Дата окончания». В выдаче у программ видны даты, подходящие по датам идут первыми.")
        state("Великобритания", screen="results", extra=VUZ)
        add(shot(pg, tmp, "06c"), "Этап 4 карты", "Великобритания: английский язык, фунты стерлингов",
            "Для Великобритании подставляются английский язык и фунты; выбор страны есть в строке поиска.")
        state("ОАЭ", screen="results", extra="S.f={level:'Бакалавриат',where:'Моя страна',year:'2027',topic:'Инженерия'};S.lang='ru';S.langManual=true")
        add(shot(pg, tmp, "06d"), "Этап 4 карты", "ОАЭ: цены в дирхамах при русском языке",
            "Валюта определяется страной, язык выбирается отдельно: русский интерфейс с ценами в дирхамах.")
        state("Россия", d="pro", screen="results", extra="S.f={interests:'Рисунок и творчество',where:'Где угодно'}")
        add(shot(pg, tmp, "07"), "Этап 4 карты", "Выдача «Профессии»: зарплатная вилка в рублях",
            "Спрос, риск автоматизации, навыки, где учиться и зарплатная вилка в месяц. Кнопка «Где учиться» передаёт профессию в подбор вуза.")
        ev("big('p3')"); pg.wait_for_timeout(300)
        add(shot(pg, tmp, "08"), "Этап 5 карты", "Профессия переходит в подбор вуза",
            "Направление переключается, фильтры подставлены: в выдаче вузы и колледжи, которые ведут к профессии.")
        state("Россия", screen="results", extra=VUZ)
        ev("big('v1')"); pg.wait_for_timeout(200)
        add(shot(pg, tmp, "09", full=False), "Этап 5 карты", "«Большая кнопка»: окно вариантов",
            "Сайт учреждения, заявка через портал (гипотеза), услуги и пакеты. Набор вариантов не утверждён.")
        ev("goSite()"); pg.wait_for_timeout(200)
        add(shot(pg, tmp, "10", full=False), "Этап 5 карты", "Просьба оставить email",
            "Перед переходом портал просит email, чтобы вернуть клиента письмом. Поле необязательное.")
        ev("closeModal();S.screen='outbound';__render()")
        add(shot(pg, tmp, "11"), "Этап 5 карты", "Сайт учреждения в новой вкладке",
            "Имитация: клиент изучает программу и подаёт заявку, вкладка портала остаётся открытой.")
        ev("__go('returned')")
        add(shot(pg, tmp, "12"), "Этап 5 карты", "Возврат и статус",
            "Клиент отмечает статус: подал, записался, пока думает.")
        ev("S.wait=['Поступление плюс виза'];__go('services')")
        add(shot(pg, tmp, "13"), "Блок 8 карты", "Услуги и пакеты", "Состав и условия не определены: вместо цен лист ожидания.")
        ev("S.quizA={0:'Придумывать и рисовать',1:'Играет в компьютерные игры',2:'Рисунок и творчество'};S.quizDone=true;__go('orient')")
        add(shot(pg, tmp, "14"), "Блок 7 карты", "Профориентация без слова в запросе",
            "Бесплатный скрининг, первые направления, подстановка в поиск профессий. Спорный пункт: что открыто, что платно.")
        ev("__go('consult')")
        add(shot(pg, tmp, "15"), "Блок 6 карты", "Консультация (статус под вопросом)", "Анкета вместо живого звонка; решения нет.")
        ev("S.saved=[{d:'vuz',n:4,date:'04.11.2026'}];S.favs=['v1','p2'];S.apps=[{t:'v1',st:'Подал заявку',kind:'сайт учреждения'}];S.consult={q:'x'};__go('cabinet')")
        add(shot(pg, tmp, "16"), "Сердечко", "Сохранённое", "Подборки, избранное, заявки и статусы, лист ожидания. Кабинет общий для всех направлений.")
        ev("__go('map')")
        add(shot(pg, tmp, "17"), "Связь с картой", "Соответствие карте", "Таблица: этап карты, узлы схемы, экран концепта, статус решения.")
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
                "Поиск как у авиабилетов: изображения, цены в валюте страны, язык страны. Поиск, подборка, сравнение, большая кнопка, возврат и кабинет по единой карте пути (04.11.2026).",
                "Концепт, не утверждён основателем. Карта: docs/html/cjm-poisk-vse-napravleniya.html; описание: docs/26, docs/28.", how, pages)
    print(out)

if __name__ == "__main__":
    main()
