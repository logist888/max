"""Resolve P07 candidates without treating a provider's paid offer as search demand."""
import argparse
import csv
import re
from collections import Counter
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("candidates", type=Path)
parser.add_argument("output", type=Path)
parser.add_argument("--ranking-keys", type=Path)
args = parser.parse_args()
ranking_keys = set(args.ranking_keys.read_text().splitlines()) if args.ranking_keys else set()

def pattern(value):
    return re.compile(value, re.IGNORECASE)

STAGES = pattern(r"(?:что (?:лучше|выбрать)|чем отличается|отличи[ея]|разница между).{0,30}(?:колледж|техникум|университет|институт|училищ[еа]|лицей|гимназия|школа|бакалавр|магистратур).{0,15}(?:или|от|и).{0,10}(?:колледж|техникум|университет|институт|училищ|лицей|гимназия|школа|бакалавр|магистратур)|^(?:community )?college (?:versus|vs\.?|or) university$|^university (?:versus|vs\.?|or) (?:community )?college$|^college or sixth form$|^(?:college|community college|university|trade school) (?:vs\.?|versus|or) (?:university|community college|trade school|college)(?: (?:in )?(?:usa|uk|canada|australia|us|america))?$|^college degree (?:vs\.?|versus) no college degree|^(?:college vs high school|university vs institute)$")
SPORT_OR_JOB = pattern(r"\b(?:football|volleyball|basketball|baseball|sports teams?|hockey|march madness|ncaa|fantasy league)\b.{0,45}(?:rank|best|школ)|(?:rank|best).{0,35}\b(?:football teams?|football recruiting|basketball|volleyball|hockey|mascots?|athletic uniforms)\b|(?:работа|зарплата|вакансия).{0,24}(?:преподавател[ея]|(?:в )?вуз.{0,10}отзыв)|school ratings sandwich|degree deodorant|youtube|школ[а-я]* магии|hentai|\banime\b|university hospital (?:ratings|reviews)")
ELIGIBILITY = pattern(r"\b(?:admission|acceptance|admit)\s+(?:chance|probability|calculator|predictor)|\b(?:gpa|sat|atar)\b.{0,35}(?:needed|required|requirements|calculator|for acceptance)|\b(?:minimum score|minimum grades?|what grades do i need|entry requirements)\b|проходно[йе].{0,18}балл|(?:шанс[ы]?|вероятность).{0,22}(?:поступ|зачисл)|балл[а-я]* для поступ")
COMPARE = pattern(r"(?:compar(?:e|isons?|ator|ador|ar|er|atif|azione)|vergleich|сравн[а-я]*|比较|比較|对比|對比|مقارنة|\bvs\.?\b|\bversus\b)")
RANKING = pattern(r"rankings?|ranked|league table|рейтинг|рэнкинг|classement|classifica|clasificaci|hochschulranking|rangliste|排名|排行榜|تصنيف|ترتيب|^qs by subject$|^arwu$")
TOP = pattern(r"\bbest\b|\btop\b|лучши[ехяй]|топ-?\s*\d+|beste[nr]?|mejor(?:es)?|miglior[ei]|meilleur")
AUTO_RANK_SOURCE = pattern(r"ranking|ranked|best[-_]|top[-_]|liste|lista|clasifica|mejores|classific|palmares|rating|reiting|reyting|timeshighereducation|topuniversities|shanghairanking|usnews|4icu|edurank|unirank|collegefactual|niche\.com/colleges/search|\.fr/.{0,15}classement")
PLACE_OR_CATEGORY = pattern(r"universit|colleg|school|mba|вуз|университет|колледж|школ|институт|licence|hochschul|[ée]cole|ateneo|大[学學]|高校|الجامع")
REVIEWS = pattern(r"\breviews?\b|\bavis\b|erfahrungen|bewertungen|opiniones|recensioni|отзыв|评价|評價|口碑|تقييم|student experience|student satisfaction")
OUTCOME = pattern(r"graduate employ|graduate outcomes|graduate salary|median earnings|job placement rate|post.?graduation (?:salary|income)|insertion (?:pro|des dipl)|emploi des dipl|occupazione laureat|ocupaci[oó]n de los graduad|трудоустройств|выпускник.{0,15}зарплат|就业率|就業率")
AGGREGATE = pattern(r"(?:acceptance|admission|admit|offer) rate|student.teacher ratio|student.staff ratio|student.to.faculty ratio|taux d.acc[eè]s|процент (?:принятых|поступивших)|college scorecard|student satisfaction survey|student satisfaction rating|survey of student")
METHODOLOGY = pattern(r"methodolog|methodik|metodolo|m[ée]thodolog|методик|方法|权重|權重|what (?:does |is )?[^ ]* ranking mean")
EDUCATIONAL_OUTCOME = pattern(r"(?:completion|graduation|retention|dropout|attrition) rates?|taux (?:de r[ée]ussite|d.abandon|de diplomation)|abschlussquote|доля завершивш|выпускаемость")
TOOL = pattern(r"\btools?\b|\bcalculator\b|\bcomparator\b|comparador|comparateur|инструмент|калькулятор|compare.{0,40}side.by.side|comparison website|vergleichsrechner|сравн[а-я]+.{0,36}онлайн|对比工具|比較工具")
PERSONAL = pattern(r"\bmy\b.{0,25}(?:college|university|schools?)|personal(?:ized|ised)? (?:college|university) rank|custom (?:college|university) rank|personal(?:ized|ised)? comparison|персональн.{0,25}(?:рейтинг|сравнен)|индивидуальн.{0,25}(?:рейтинг|сравнен)|по моим критериям|個人化排名|个性化排名")
PAID_RESULT = pattern(r"(?:\b(?:buy|order|purchase|pay for|price of|subscribe to|paid|cost of)\b|заказ[а-я]*|купить|платн[а-я]*|стоимость|цен[аыу]|acheter|tarif|prix|kaufen|kosten|preis|comprar|precio|tariffa|购买|購買).{0,60}(?:(?:compar(?:ison|atif|ador|ateur)|сравнен|vergleich).{0,25}(?:report|analysis|отч[её]т|rapport|analisi|informe|bericht)|college compass|(?:college|university)\s+(?:compass|premium fit report))|(?:сравн[а-я]+.{0,40}отч[её]т|compar(?:ison|ative) report|college compass|premium fit report|rapport comparatif).{0,25}(?:pricing|price|cost|цена|купить|стоимость|заказать|prix|precio|preis)")
PRICE = pattern(r"\b(?:price|pricing|cost)\b|цен[аыу]|стоимость|prix|precio|preis")

def resolve(row):
    query = row["query_normalized"]
    target = row["target_url"]
    lexical = row["lexical_cluster"]
    prior = row["prior_cluster"]
    cluster = lexical or row["cluster"]
    if row["resolution"] == "excluded" or SPORT_OR_JOB.search(query) or re.search(r"\b(?:conseill[èe]r|conseill[èe]re|charg[ée]e?|m[ée]tier)\b.{0,35}insertion professionnelle|university of oxford vs oxford university|oxford university vs university of oxford", query):
        return "exclude", cluster, "", "", "Вне образовательного сравнения либо отзывы работодателя"
    if STAGES.search(query) or re.search(r"(?:лучши|рейтинг).{0,12}общежит|best (?:college|university) dorms?", query):
        return "adjacent", cluster, "", "", "P02: различия форм или ступеней без сравнения именованных вариантов"
    if ELIGIBILITY.search(query):
        return "adjacent", cluster, "", "", "P09: условия или персональные шансы на допуск"
    if PAID_RESULT.search(query) and (COMPARE.search(query) or "compass" in query or "fit report" in query):
        return "accept", "K022", "D3", "I10" if PRICE.search(query) else "I11", "Явный запрос цены или заказа сравнительного результата"
    if cluster == "P07-K30" or (METHODOLOGY.search(query) and RANKING.search(query)):
        return "accept", "P07-K30", "D1", "I04", "Запрос методики, весов или трактовки рейтинга"
    if cluster == "P07-K31" or (EDUCATIONAL_OUTCOME.search(query) and prior == "K123"):
        return "accept", "P07-K31", "D1", "I04", "Образовательный исход или удержание когорты"
    if cluster == "K028" and (lexical or OUTCOME.search(query) or "employment" in query) and (not re.search(r"insertion professionnelle", query) or re.search(r"dipl[oô]m|sortants?|universit|licence|master|bts|formation|(?:taux|statistique).{0,35}insertion", query)):
        return "accept", cluster, "D1", "I04", "Результаты выпускников, включая трудоустройство и заработок"
    if cluster == "K022" and (COMPARE.search(query) or lexical and PERSONAL.search(query)):
        if PERSONAL.search(query):
            return "accept", cluster, "D2", "I05", "Персональная матрица, веса или рейтинг по своим критериям"
        if TOOL.search(query):
            return "accept", cluster, "D2", "I07", "Явный запрос инструмента или результата сравнения рядом"
        if any(x in query for x in ("compare schools", "compare colleges", "compare universities")) or lexical or PLACE_OR_CATEGORY.search(query):
            return "accept", cluster, "D1", "I03", "Сопоставление образовательных вариантов"
    if cluster == "K027" and REVIEWS.search(query):
        if prior == "K027" or lexical:
            return "accept", cluster, "D1", "I04", "Опыт и отзывы об учебном объекте"
    if cluster == "K123" and AGGREGATE.search(query):
        return "accept", cluster, "D1", "I04", "Измерение учреждения или потока; первичный показатель отдельно от допуска"
    if cluster == "K026":
        if RANKING.search(query) or lexical and any(x in query for x in ("shanghai ranking", "hochschulranking")):
            return "accept", cluster, "D1", "I03", "Запрос позиции, методики ранжирования или табличного рейтинга"
        if TOP.search(query) and (AUTO_RANK_SOURCE.search(target) or row["query_id"] in ranking_keys):
            return "accept", cluster, "D1", "I03", "Запрос о лучших вариантах, связанный с ранжированным источником"
        if TOP.search(query):
            return "adjacent", cluster, "", "", "Широкий поиск лучших вариантов; нет однозначного признака рейтинговой страницы"
    return "ambient", cluster, "", "", "Навигация, вторичная метка либо неустановленная связь с результатом P07"

with args.candidates.open(encoding="utf-8-sig", newline="") as source, args.output.open("w", encoding="utf-8", newline="") as sink:
    reader = csv.DictReader(source)
    writer = csv.writer(sink)
    writer.writerow(("query_id", "decision", "cluster", "evidence", "intent", "note"))
    counts = Counter()
    for row in reader:
        result = resolve(row)
        counts[(result[0], result[1], result[2])] += 1
        writer.writerow((row["query_id"], *result))
    for result, count in sorted(counts.items()):
        print(*result, count, sep="\t")
