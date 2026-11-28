"""Deterministic routing of education search phrases. Source text remains unchanged."""
from __future__ import annotations

import csv
import re
import unicodedata
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path
from re import _constants, _parser

CONFIG = Path(__file__).with_name("config")
LANGUAGES = ("en", "ru", "de", "fr", "it", "es", "zh", "ar")
PRIORITY = {
    "K001": 35, "K012": 45, "K022": 45, "K023": 30, "K025": -10,
    "K024": -10, "K033": 50, "K034": 55, "K038": 55, "K043": 50,
    "K045": 38, "K047": 25, "K049": 3, "K054": 40, "K062": 25,
    "K066": -10, "K068": 25, "K069": 45, "K073": 45, "K074": 48,
    "K075": 26, "K076": 36, "K077": 40, "K078": 38, "K079": 40,
    "K080": 45, "K081": -40, "K087": -15, "K088": 40, "K095": 30,
    "K096": 28, "K097": 38, "K103": 42, "K111": -100, "K112": -20,
    "K113": -100, "K116": 45, "K117": 85, "K118": 85, "K119": 85,
    "K120": 85, "K121": 80, "K122": 80, "K126": 40, "K128": 60,
    "K129": 80, "K130": 80,
}

with (CONFIG / "cluster_rules.tsv").open(encoding="utf-8", newline="") as stream:
    RULES = list(csv.DictReader(stream, delimiter="\t"))
CLUSTERS = {
    row["CLUSTER_BASE_ID"]: {
        key: row[key] for key in (
            "CLUSTER_BASE_ID", "TASK_ID", "SERVICE_ID", "DEFAULT_INTENT", "CLUSTER_NAME"
        )
    } | {"Q_ID": row["TASK_ID"].split(".", 1)[0]}
    for row in RULES
}
PRIORITY.update({
    "K073": 68, "K118": 85, "K103": 65, "K054": 70, "K047": 38,
    "K131": 50, "K132": 68, "K133": 72, "K134": 62, "K135": 55,
    "K136": 20, "K137": -8, "K138": 8, "K139": 55, "K140": 8, "K141": 57,
})


def _mandatory_literals(nodes) -> tuple[str, ...]:
    """Choose a nonempty disjunction guaranteed to occur in regex matches."""
    choices = []
    run = []
    for op, arg in nodes:
        if op is _constants.LITERAL:
            run.append(chr(arg))
            continue
        if run:
            choices.append(("".join(run),))
            run = []
        if op is _constants.BRANCH:
            branch_literals = [_mandatory_literals(branch) for branch in arg[1]]
            if all(branch_literals):
                choices.append(tuple(seed for branch in branch_literals for seed in branch))
        elif op is _constants.SUBPATTERN:
            literal = _mandatory_literals(arg[-1])
            if literal:
                choices.append(literal)
        elif op in {_constants.MAX_REPEAT, _constants.MIN_REPEAT, _constants.POSSESSIVE_REPEAT} and arg[0]:
            literal = _mandatory_literals(arg[-1])
            if literal:
                choices.append(literal)
    if run:
        choices.append(("".join(run),))
    return max(choices, key=lambda c: (min(map(len, c)), -len(c)), default=())


def _indexed_rules(language):
    expressions = {row["CLUSTER_BASE_ID"]: row[language] for row in RULES if row[language]}
    gram_size = 2 if language == "zh" else 3
    tables = {
        base: re.compile(expression if language == "zh" else f"(?<!\\w)(?:{expression})(?!\\w)")
        for base, expression in expressions.items()
    }

    def grams(word):
        return frozenset(
            word[offset:offset + gram_size]
            for offset in range(len(word) - gram_size + 1)
        )

    frequency = Counter(gram for pattern in expressions.values() for gram in grams(pattern))
    index = defaultdict(set)
    unindexed = set()
    for base, expression in expressions.items():
        seeds = _mandatory_literals(_parser.parse(expression, 0))
        candidates = [grams(seed) for seed in seeds]
        if not candidates or not all(candidates):
            unindexed.add(base)
            continue
        for options in candidates:
            rare = min(options, key=lambda gram: (frequency[gram], not gram.isalnum(), gram))
            index[rare].add(base)
    return tables, dict(index), frozenset(unindexed), gram_size


SIGNALS = {language: _indexed_rules(language) for language in LANGUAGES}

# Language detection is independent of country and script variants remain in the source.
SCRIPT = re.compile(
    r"(?P<cyr>[\u0400-\u052f])|(?P<arab>[\u0600-\u06ff\u0750-\u077f])|"
    r"(?P<han>[\u3400-\u9fff])|(?P<kana>[\u3040-\u30ff])|(?P<hangul>[\uac00-\ud7af])|"
    r"(?P<deva>[\u0900-\u097f])|(?P<thai>[\u0e00-\u0e7f])|(?P<hebr>[\u0590-\u05ff])"
)
MARKET_LANGUAGES = {
    "RU": ("ru", "en"), "UK": ("en",), "GB": ("en",), "US": ("en",),
    "CA": ("en", "fr"), "CH": ("de", "fr", "it", "en"), "FR": ("fr", "en"),
    "IT": ("it", "en"), "ES": ("es", "en"), "AE": ("en", "ar"),
    "SG": ("en", "zh"), "HK": ("en", "zh"), "CN": ("zh", "en"),
    "DE": ("de", "en"), "AU": ("en",), "AT": ("de", "en"),
    "BE": ("fr", "en"), "LU": ("fr", "de", "en"), "MX": ("es", "en"),
}
FINGERPRINTS = {
    "en": "about and what which how when where is are your you your tuition college colleges universities school schools scholarship scholarships degree degrees graduate abroad academic admission admissions requirements apply student students cost university for the online of".split(),
    "de": "wie darf welche welcher fur mit von zur zum und der das hochschule hochschulen universitat universitaten schule studium studiengang ausbildung bewerbung zulassung studierende kosten".split(),
    "fr": "comment quand quel quelle quels et aux des une pour avec sans universite universites etudes etudiant etudiants parcoursup bourse formation formations cours frais scolaire ecole ecoles".split(),
    "it": "come quale quando quali con senza della degli delle iscrizione immatricolazione laurea universita corsi corso ammissione orario borse borsa studenti scuola scuole".split(),
    "es": "como cual cuales donde cuando para los las una sin con universidad universidades beca becas escuela colegios estudio estudios grado maestria requisitos estudiantes cursos admision matricula".split(),
    "pt": "como quais onde nao inscricao educacao vestibular faculdade universidades mestrado graduacao estudante bolsas ensino".split(),
    "nl": "waar welke wanneer voor zijn opleiding opleidingen universiteit studeren studie studiefinanciering".split(),
}
FINGERPRINTS = {language: frozenset(tokens) for language, tokens in FINGERPRINTS.items()}
# Limited, auditable variants frequently encountered in Hong Kong terms.
HAN_MAP = str.maketrans(dict(zip(
    "學術職業測試專選規劃錄報條與無辦許證課實習經歷認異計數額資費錢獎獲來查申轉繳灣國議諮詢輔導領註獨書發會開關簡介醫師語碩讀分鐘實驗應現盡預練預訓學",
    "学术职业测试专选规划录报条与无办许证课实习经历认异计数额资费钱奖获来查申转缴湾国议咨询辅导领注独书发会开关简介医师语硕读分钟实验应现尽预练预训学",
    strict=True,
)))
ARABIC_MAP = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي", "ـ": ""})
APOSTROPHES = str.maketrans({"’": "'", "‘": "'", "ʻ": "'", "ʼ": "'", "‐": "-", "‑": "-", "–": "-", "—": "-"})
ASCII_TOKEN = re.compile(r"[a-z]{2,}")
WS = re.compile(r"\s+")
URL_OR_EMAIL = re.compile(r"^(?:https?://|www\.)|^[^ ]+@[^ ]+$")
OFF_TOPIC = re.compile(
    r"^(?:weather(?: forecast)?|meteo|погода|博彩|porn|porno|bitcoin price|ethereum price|"
    r"football live|live cricket score|crypto price|recette de cuisine|ricetta (?:pizza|pasta)|"
    r"купить диплом без обучени\w*|fake diploma (?:buy|for sale)|假文凭购买)\b"
)
NAV_ABBREVIATION = re.compile(r"^[a-z0-9. -]{2,9}$")
QUESTION_PREFIX = re.compile(
    r"^(?:what|how|when|where|why|which|was|wie|wann|warum|wo|quel(?:le)?|comment|quand|"
    r"quanto|quale|cosa|come|quando|dove|como|que|cual|donde|когда|что|какой|где|как)\b|"
    r"^(?:什么|怎么|如何|几时|哪里|متى|ما هو|كيف|اين|لماذا)"
)
TOOL = re.compile(
    r"(?:calculat(?:or|eur|rice|ora)|simulat(?:or|eur|ore|ador)|rechner|checker|matcher|"
    r"калькулятор|симулятор|тренажер|генератор|计算器|模拟器|评估工具|حاسبة|محاكي)"
)
DOCUMENT = re.compile(
    r"\b(?:template|sample|example|pdf|exemple|modele|muster|vorlage|"
    r"modello|ejemplo|plantilla|образец|шаблон|пример)\b|范文|样本|模板|نموذج"
)
TRACKING = re.compile(
    r"\b(?:track(?:er|ing)?|alert(?:s)?|notification(?:s)?|rappel|"
    r"benachrichtigung|promemoria|avviso|recordatorio|alerta)\b|трекер|уведомлен|напоминан|"
    r"进度表|提醒|تذكير|متتبع"
)
TRANSACTION = re.compile(
    r"\b(?:buy|purchase|order|pay for|hire|book|paid|kaufen|buchen|bestellen|beauftragen|"
    r"acheter|commander|reserver|payant|comprare|acquistare|prenotare|"
    r"comprar|contratar|reservar|заказать|купить|платн\w*|нанять|под ключ)\b|"
    r"购买|订购|付费|下单|شراء|توظيف|مدفوع|احجز"
)
PRICE = re.compile(
    r"\b(?:prices?|pricing|costs?|fees?|kosten|preise?|prix|tarifs?|costo|prezzo|precio|cuanto cuesta|"
    r"тариф\w*|сколько стоит|стоимост\w*|цен[аыуе])\b|收费|收費|多少钱|价格|السعر|التكلفة"
)
FREE = re.compile(
    r"\b(?:free|freely|kostenlos|gratuit\w*|gratis|бесплатн\w*|без оплат\w*)\b|免费|مجاني"
)
PROFESSIONAL = re.compile(
    r"\b(?:consultant\w*|consulting|coach\w*|tutor\w*|advisor\w*|counselor\w*|agency|agent|"
    r"beratung|berater\w*|nachhilfe|service\w*|lektorat|correcteur\w*|consultant\w*|"
    r"accompagnement|agence|consulente|consulenz\w*|servizi\w*|asesor\w*|gestoria|"
    r"репетитор\w*|консультант\w*|агентств\w*|редактор\w*|услуг\w*)\b|"
    r"顾问|中介|代办|服务|مستشار|وكيل|خدمة|مدرس خصوصي"
)
DIRECT_SERVICE = frozenset({"K103", "K117", "K118", "K119", "K120"})
COMMERCIAL_EXPLICIT = re.compile(
    r"\b(?:proofread\w*|editor\w*|editing|professional|expert|independent|private|"
    r"prive\w*|payant\w*|professionnel\w*|privat\w*|privad\w*|profesion\w*|"
    r"редактур\w*|платн\w*)\b|收费|付费|价格|مقابل رسوم"
)
OWN_QUOTE_ELIGIBLE = frozenset({"K001", "K002", "K012", "K052", "K054", "K095", "K097", "K117", "K118", "K119", "K120", "K129", "K130", "K141"})
VISAFEE = re.compile(r"visa.{0,26}\b(?:fee|cost|payment)\b|визов\w* сбор|签证费|رسوم التأشيرة")
SOCIAL_SERVICE = frozenset({"K001", "K002", "K012", "K022", "K023", "K033", "K038", "K049", "K051", "K052", "K054", "K057", "K062", "K064", "K069", "K075", "K081", "K087", "K089", "K095", "K097", "K098", "K113", "K121", "K125", "K128", "K129", "K130", "K141"})
EXTERNAL = frozenset({"K040", "K041", "K042", "K045", "K056", "K059", "K065", "K066", "K067", "K071", "K078", "K083", "K085", "K088", "K109", "K116", "K122", "K134"})
FREETEXT_DOCS = frozenset({"K049", "K050", "K075", "K099"})
UTILITY = frozenset({"K001", "K023", "K038", "K043", "K069", "K097", "K098", "K121", "K128", "K141"})
DIMENSIONS = {
    "LEARNING_LEVEL": (
        ("early_childhood", r"preschool|kindergarten|maternelle|дошкольн|детский сад|幼儿园|روضة"),
        ("primary", r"primary school|elementary school|ecole primaire|grundschule|escuela primaria|начальн\w* школ|小学|المرحلة الابتدائية"),
        ("secondary", r"high school|secondary school|sixth form|gymnasium|lycee|bachillerato|старш\w* школ|средн\w* школ|高中|ثانوية"),
        ("vocational", r"vocational|apprentice|ausbildung|formation professionnelle|formacion profesional|\bспо\b|профпереподготовк|职校|التدريب المهني"),
        ("bachelor", r"bachelor|undergraduate|laurea triennale|бакалавр|本科|بكالوريوس"),
        ("master", r"\bmasters?\b|postgraduate|magister|maestria|магистр|硕士|ماجستير"),
        ("doctorate", r"\bph\.?d\b|doctorate|doktorand|doctorat|dottorato|doctorado|аспирантур|докторантур|博士|دكتوراه"),
    ),
    "PROGRAM_TYPE": (
        ("language", r"language (course|school)|sprachkurs|cours de langue|corso di lingua|cursos de idioma|языков\w* курс|语言课程|دورات لغة"),
        ("summer", r"summer (school|camp|course)|sommercamp|camps? d.ete|corsi estivi|летн\w* (школ|лагер)|夏令营|暑期学校|مخيمات صيفية"),
        ("exchange", r"exchange program|austauschprogramm|programme d.echange|programma di scambio|programa de intercambio|обмен\w* студент|交换项目|برنامج تبادل"),
        ("test_prep", r"\bprep\b|prufungsvorbereitung|preparation au concours|репетитор|подготовк\w* к (егэ|огэ|экзамен)|高考辅导|تحضير للاختبار"),
        ("online", r"\bonline\b|distance learning|fernstudium|distanciel|en linea|дистанционн|онлайн|线上|عن بعد"),
        ("short_course", r"short cours|microcredential|kurzkurs|formation courte|cursos cortos|краткосрочн\w* курс|短期课程|دورات قصيرة"),
        ("executive", r"\b(?:mba|emba|executive education)\b|бизнес.образован|工商管理硕士"),
    ),
    "ROLE": (
        ("parent", r"\b(?:for my child|for parents|pour mon enfant|fur mein kind|para mi hijo)\b|для (моего ребенка|родител)|家长|للوالدين"),
        ("current_learner", r"current student|student login|already enrolled|действующ\w* студент|уже учусь|在校生|طالب حالي"),
        ("international_applicant", r"international (student|applicant)|foreign (student|applicant)|auslandische studierende|etudiant etranger|иностранн\w* (студент|абитуриент)|留学生|طالب دولي"),
        ("adult", r"adult learner|mature student|erwachsenenbildung|formation adultes|для взросл\w*|成人教育|تعليم الكبار"),
    ),
}
DIMENSIONS = {key: tuple((code, re.compile(pattern)) for code, pattern in values) for key, values in DIMENSIONS.items()}

COUNTRY_NAMES = {
    "RU": r"russia|russie|russland|rusia|russia|росси[июя]|москв[еау]|俄罗斯|روسيا",
    "GB": r"uk|united kingdom|great britain|england|royaume.?uni|grossbritannien|inghilterra|reino unido|великобритани[июя]|англи[июя]|英国|المملكة المتحدة|بريطانيا",
    "US": r"us|u\.s\.|usa|united states(?: of america)?|etats.?unis|vereinigte staaten|stati uniti|estados unidos|сша|америк[еуи]|美国|الولايات المتحدة",
    "CA": r"canada|kanada|канад[еуи]|加拿大|كندا",
    "CH": r"switzerland|schweiz|suisse|svizzera|suiza|швейцари[июя]|瑞士|سويسرا",
    "FR": r"france|frankreich|francia|франци[июя]|法国|فرنسا",
    "IT": r"italy|italien|italie|italia|итали[июя]|意大利|ايطاليا",
    "ES": r"spain|spanien|espagne|espana|spagna|испани[июя]|西班牙|اسبانيا",
    "AE": r"united arab emirates|uae|dubai|abu dhabi|emirats arabes unis|emiratos arabes unidos|оаэ|дуба[ией]|阿联酋|迪拜|الامارات|دبي",
    "SG": r"singapore|singapour|singapur|сингапур[ае]?|新加坡|سنغافورة",
    "HK": r"hong kong|hongkong|гонконг[ае]?|香港|هونغ كونغ",
    "CN": r"china|chine|cina|кита[еяй]|中国|الصين",
    "DE": r"germany|deutschland|allemagne|germania|alemania|германи[июя]|德国|المانيا",
    "AU": r"australia|australien|australie|австрали[июя]|澳大利亚|استراليا",
}
COUNTRIES = "|".join(f"(?P<{code}>{pattern})" for code, pattern in COUNTRY_NAMES.items())
DEST_AFTER = re.compile(
    r"(?:\b(?:study|studying|studies|universities|colleges|schools|degree|masters|scholarships) (?:in|at|en|au|a)\s+(?:the )?|"
    r"\b(?:studieren|studium|hochschulen) in\s+|\b(?:etudier|etudes|universites|formation) (?:en|au|aux|a)\s+|"
    r"\b(?:studiare|universita|laurea) (?:in|a|negli)\s+|\b(?:estudiar|universidades|carreras) en\s+|"
    r"\b(?:обучен\w*|учиться|учеб\w*|вуз\w*|стипенди\w*) (?:в|на)\s+|(?:الدراسة|جامعات|التعليم) في\s+)"
    f"(?:{COUNTRIES})(?!\\w)"
)
DEST_BEFORE = re.compile(
    f"(?<![a-z])(?:{COUNTRIES})(?:\\s+(?:student visa|study visa|study permit|universities)\\b|(?:留学|读大学|大学申请))"
)


def _fold(value: str) -> str:
    text = unicodedata.normalize("NFKC", value).casefold().translate(APOSTROPHES)
    if text.isascii():
        return WS.sub(" ", text).strip()
    text = text.translate(HAN_MAP).translate(ARABIC_MAP).replace("ё", "е")
    output = []
    for character in text:
        if ord(character) < 128:
            output.append(character)
        elif unicodedata.category(character) == "Mn":
            continue
        elif "LATIN" in unicodedata.name(character, ""):
            output.append("".join(
                item for item in unicodedata.normalize("NFKD", character)
                if unicodedata.category(item) != "Mn"
            ))
        else:
            output.append(character)
    return WS.sub(" ", "".join(output)).strip()


RAW_LANGUAGES = {
    "english": "en", "russian": "ru", "german": "de", "french": "fr",
    "italian": "it", "spanish": "es", "chinese": "zh", "chinese (simplified)": "zh",
    "chinese (traditional)": "zh", "arabic": "ar", "japanese": "ja", "korean": "ko",
    "portuguese": "pt", "dutch": "nl", "thai": "th", "hebrew": "he",
    "ukrainian": "uk", "hindi": "hi", "vietnamese": "vi", "persian": "fa",
}
RAW_LANGUAGES.update({code: code for code in tuple(RAW_LANGUAGES.values())})


def _language(folded: str, source_language: str | None) -> tuple[str, str]:
    if not folded.isascii():
        scripts = {hit.lastgroup for hit in SCRIPT.finditer(folded)}
        if "kana" in scripts:
            return "ja", "script"
        if "hangul" in scripts:
            return "ko", "script"
        if "han" in scripts:
            return "zh", "script"
        if "arab" in scripts:
            if any(character in folded for character in "پچگژ"):
                return "und", "ambiguous_script"
            return "ar", "script"
        if "cyr" in scripts:
            return ("uk" if any(character in folded for character in "іїєґ") else "ru"), "script"
        if "deva" in scripts:
            return "und", "ambiguous_script"
        if "thai" in scripts:
            return "th", "script"
        if "hebr" in scripts:
            return "he", "script"
    if source_language:
        return source_language, "provider"
    tokens = frozenset(ASCII_TOKEN.findall(folded))
    if not tokens:
        return "und", "unresolved"
    scores = Counter({code: len(tokens & lexicon) for code, lexicon in FINGERPRINTS.items()})
    first, second = scores.most_common(2)
    if first[1] and first[1] > second[1]:
        return first[0], "lexical"
    return "und", "unresolved"


def _destination(folded: str) -> str | None:
    matches = {match.lastgroup for search in (DEST_AFTER, DEST_BEFORE) for match in search.finditer(folded)}
    return next(iter(matches)) if len(matches) == 1 else None


def _intent(folded: str, base: str, default: str) -> tuple[str, str, str | None]:
    # Payment to a university, examination board, official portal or authority.
    if base in EXTERNAL:
        return default, "D1", "external_institution_or_authority"
    if default in {"I12", "I14"}:
        return default, "D1", None
    free = bool(FREE.search(folded))
    question = bool(QUESTION_PREFIX.search(folded))
    document = bool(DOCUMENT.search(folded))
    provider = bool(PROFESSIONAL.search(folded))
    price, transaction = bool(PRICE.search(folded)), bool(TRANSACTION.search(folded))

    if not free and not document:
        explicit = bool(COMMERCIAL_EXPLICIT.search(folded))
        provider_query = (base in DIRECT_SERVICE and (provider or explicit)) or (base in SOCIAL_SERVICE and provider)
        paid_result = base in OWN_QUOTE_ELIGIBLE and (price or transaction)
        if provider_query or paid_result:
            return (
                "I11" if transaction else "I10" if price else "I09",
                "D3",
                "third_party_service",
            )
    if base == "K081" and VISAFEE.search(folded):
        return "I15" if re.search(r"payment|pay|оплат|缴费|دفع", folded) else "I01", "D1", "external_institution_or_authority"

    if TOOL.search(folded):
        return "I06" if default == "I06" else "I07", "D2", None
    if TRACKING.search(folded) and base in {"K017", "K018", "K047", "K121", "K128"}:
        return "I13", "D2", None
    if document and base in FREETEXT_DOCS | {"K096", "K098"}:
        return "I08", "D2", None
    if base in UTILITY:
        return default, "D2", None
    if base in {"K033", "K054", "K118", "K119"} and not question:
        return "I05" if default == "I09" else default, "D2", None
    if base in FREETEXT_DOCS or (default == "I09" and free):
        return "I01" if default != "I09" else "I09", "D1", None
    return default, "D1", None


def _route(folded: str, language: str, market: str) -> tuple[list[tuple[str, int, str]], str | None]:
    if language in LANGUAGES:
        candidates = (language,) if not folded.isascii() else tuple(dict.fromkeys((language, "en")))
    elif language == "und" and folded.isascii():
        candidates = MARKET_LANGUAGES.get(market, ("en", "de", "fr", "it", "es"))
    else:
        return [], None

    for candidate in candidates:
        tables, index, unindexed, gram_size = SIGNALS[candidate]
        shortlist = set(unindexed)
        for position in range(len(folded) - gram_size + 1):
            related = index.get(folded[position:position + gram_size])
            if related:
                shortlist.update(related)
        hits = []
        for base in shortlist:
            if (match := tables[base].search(folded)):
                hits.append((base, len(match.group()), match.group()))
        if hits:
            return hits, candidate
    return [], None


@lru_cache(maxsize=40_000)
def _classify(folded: str, market: str, source_language: str | None, provider_navigation: bool) -> dict:
    language, language_source = _language(folded, source_language)
    result = {
        "LANGUAGE": language,
        "LANGUAGE_SOURCE": language_source,
        "INTENT_ID": None,
        "CLUSTER_BASE_ID": None,
        "CLUSTER_ID": None,
        "SUBCLUSTER_ID": None,
        "Q_ID": None,
        "TASK_ID": None,
        "TASK_HINT": None,
        "SERVICE_ID": None,
        "RELEVANCE": "unresolved",
        "CONFIDENCE": 0.0,
        "SECONDARY_CLUSTERS": (),
        "EVIDENCE_LEVEL": "D0",
        "ACTION_PAYEE": None,
        "LEARNING_LEVEL": None,
        "PROGRAM_TYPE": None,
        "ROLE": None,
        "DESTINATION_HINT": None,
        "QUERY_TRANSLATION": None,
        "LIMITATIONS": "no_matching_rule",
    }
    if not folded or URL_OR_EMAIL.search(folded) or OFF_TOPIC.search(folded):
        result["RELEVANCE"] = "excluded_explicit"
        result["LIMITATIONS"] = "explicit_exclusion"
        return result

    hits, pattern_language = _route(folded, language, market)
    if not hits:
        if provider_navigation:
            result["RELEVANCE"] = "provider_navigation_unresolved"
        result["DESTINATION_HINT"] = _destination(folded)
        return result

    hits.sort(key=lambda hit: (-PRIORITY.get(hit[0], 0), -hit[1], hit[0]))
    base, match_len, match_text = hits[0]
    if language == "und" and pattern_language and not NAV_ABBREVIATION.fullmatch(match_text):
        language, language_source = pattern_language, "pattern"
    info = CLUSTERS[base]
    intent, evidence, payee = _intent(folded, base, info["DEFAULT_INTENT"])
    cluster = f"{base}-{intent}"
    if intent == "I12":
        relev = "navigation"
    elif intent == "I14":
        relev = "continuation"
    elif payee == "external_institution_or_authority" and intent == "I15":
        relev = "external_action"
    elif evidence == "D3":
        relev = "commercial"
    else:
        relev = "relevant"
    service = None if relev in {"navigation", "continuation", "external_action"} else info["SERVICE_ID"] or None
    additional = tuple(dict.fromkeys(
        hit[0] for hit in hits if CLUSTERS[hit[0]]["TASK_ID"] != info["TASK_ID"]
    ))
    result.update({
        "LANGUAGE": language,
        "LANGUAGE_SOURCE": language_source,
        "INTENT_ID": intent,
        "CLUSTER_BASE_ID": base,
        "CLUSTER_ID": cluster,
        "SUBCLUSTER_ID": f"{cluster}:{market or 'und'}:{language}",
        "Q_ID": info["Q_ID"],
        "TASK_ID": info["TASK_ID"],
        "TASK_HINT": info["CLUSTER_NAME"],
        "SERVICE_ID": service,
        "RELEVANCE": relev,
        "CONFIDENCE": (
            0.72 if base in {"K111", "K113"} or language == "und" or language_source == "pattern"
            else 0.85 if match_len <= 9 or additional
            else 0.93
        ),
        "SECONDARY_CLUSTERS": additional,
        "EVIDENCE_LEVEL": evidence,
        "ACTION_PAYEE": payee,
        "DESTINATION_HINT": _destination(folded),
        "LIMITATIONS": "multiple_task_candidates" if additional else "dictionary_classification",
    })
    for key, alternatives in DIMENSIONS.items():
        result[key] = next((code for code, pattern in alternatives if pattern.search(folded)), None)
    return result


def classify(query: str, target_url: str = "", market: str | None = None,
             *, language_raw: str | None = None, branded: bool | None = None,
             navigational: bool | None = None) -> dict:
    """Classify verbatim phrase. A source URL never upgrades commercial evidence."""
    market_code = str(market or "").strip().upper()
    if market_code in {"", "GLOBAL", "UNKNOWN", "NONE", "UND", "NULL", "WORLDWIDE", "WW"}:
        market_code = ""
    source_language = RAW_LANGUAGES.get(str(language_raw or "").strip().strip('"').casefold())
    return dict(_classify(
        _fold(query or ""), market_code, source_language,
        branded is True and navigational is True,
    ))


def write_catalog() -> None:
    path = CONFIG / "cluster_catalog.tsv"
    fields = ("CLUSTER_BASE_ID", "Q_ID", "TASK_ID", "SERVICE_ID", "DEFAULT_INTENT", "CLUSTER_NAME")
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(CLUSTERS.values())


if __name__ == "__main__":
    write_catalog()
