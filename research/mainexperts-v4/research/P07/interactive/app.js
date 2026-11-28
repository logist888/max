"use strict";

(async function start(){
const payload = document.getElementById("research-data");
const bytes = Uint8Array.from(atob(payload.textContent.trim()), ch => ch.charCodeAt(0));
const packed = await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream("gzip"))).json();
payload.remove();
function unpack([keys, values]) {
  return values.map(row => Object.fromEntries(keys.map((key, index) => [key, row[index]])));
}
const data = Object.fromEntries(Object.entries(packed).map(([key, value]) => [key, key === "coverage" ? value : unpack(value)]));
const cv = data.coverage;
const app = document.getElementById("app");
const detail = document.getElementById("detail");
const lightbox = document.getElementById("lightbox");
const byId = rows => new Map(rows.map(row => [row.id, row]));
function group(rows, key) {
  const index = new Map();
  for (const row of rows) {
    const value = row[key];
    if (!index.has(value)) index.set(value, []);
    index.get(value).push(row);
  }
  return index;
}
const projects = byId(data.projects);
const queries = byId(data.queries);
const routes = byId(data.routes);
const shots = byId(data.shots);
const sources = byId(data.sources);
const obsByQuery = group(data.observations, "query");
const obsByProject = group(data.observations, "project");
const routesByProject = group(data.routes, "project");
const stepsByRoute = group(data.steps, "route");
const linksByQuery = group(data.routeObservations, "query");
const linksByRoute = group(data.routeObservations, "route");
const shotsByRoute = group(data.shotLinks, "route");
const landingsByProject = group(data.landings, "project");
const hitsByProject = new Map(Array.from(obsByProject, ([id, rows]) => [id, new Set(rows.map(row => row.query))]));
const hitsByRoute = new Map(Array.from(linksByRoute, ([id, rows]) => [id, new Set(rows.map(row => row.query))]));
const querySearchIndex = new Map();
for (const q of data.queries) {
  const seen = new Set((obsByQuery.get(q.id) || []).map(o => o.raw));
  querySearchIndex.set(q.id, norm([q.raw, q.normalized, q.cluster, q.task, ...seen].join(" ")));
}

const labels = cv.cluster_names;
const intents = {
  I01:"Узнать и разобраться", I02:"Найти варианты", I03:"Сопоставить варианты", I04:"Проверить показатель или основание", I05:"Получить персональную оценку",
  I07:"Найти инструмент", I08:"Получить готовый результат", I09:"Найти специалиста", I10:"Узнать цену", I11:"Заказать или купить услугу", I12:"Найти поставщика или официальный источник", I13:"Отслеживать изменения",
};
const levels = {D1:"Информационный спрос",D2:"Инструмент или персональный результат",D3:"Коммерческое намерение"};
const languages = {ru:"Русский",en:"Английский",fr:"Французский",de:"Немецкий",es:"Испанский",it:"Итальянский",zh:"Китайский",vi:"Вьетнамский",und:"Язык не установлен"};
const metrics = {keys_exact:"Точная оценка Keys",ahrefs_volume:"Рыночная оценка Ahrefs",ahrefs_top_location_volume:"Оценка ведущего рынка Ahrefs",vendor_unspecified:"Методика источника не указана"};
const scopes = {
  exact_included_url:"Исходная посадочная",additional_route_of_corpus_project:"Другой маршрут проекта из корпуса",
  external_benchmark:"Внешний аналог",adjacent_or_excluded:"Смежный или исключённый маршрут",other_observed_route:"Отдельная проверка",
};
const outcomes = {
  free_entry_result_unverified:"Бесплатный вход, результат не проверен",public_answer:"Публичный ответ",
  public_referral:"Публичный переход", public_lead:"Заявка или контакт",partner_lead:"Партнёрская заявка",priced_lead:"Цена и запись",checkout_observed:"Наблюдалось оформление до оплаты",priced_export:"Платный экспорт",planned_no_checkout:"Планируемый тариф",free_public_path:"Публичный бесплатный путь",
  free_result_observed:"Бесплатный результат наблюдался",access_limited:"Доступ ограничен",excluded:"Исключён",
  adjacent_catalog:"Смежный каталог",adjacent_monetization:"Открытый ответ и оплата смежного шага",adjacent_content:"Смежный материал",buy_cta_only:"Кнопка покупки видна",
  institutional_paid:"Платит организация",priced_precondition:"Видна цена, дальнейшие шаги ограничены",official_free_channel:"Открытый официальный канал",registration_gate:"Требуется вход",
};
const feedStates = {
  page_text_opened:"Текст страницы получен",no_indexed_text:"В индексе нет пригодного текста",
  fetch_blocked:"Ошибка получения страницы",sparse_content:"Короткий или технический ответ",
  no_result:"Ответ по адресу не получен", readable_excerpt:"Есть доступный фрагмент текста", reader_error:"Чтение URL вернуло ошибку", no_visible_result:"Чтение не вернуло наблюдение", reader_not_attempted:"Нет отдельной проверки адреса", route_reviewed:"Адрес сопоставлен с маршрутом",not_addressable:"Адрес не указан",
};
const verification = {
  browser_screenshot:"Браузерный кадр", live_questions:"Вопросы открыты в браузере",
  result_observed:"Результат получен", public_text_reviewed:"Прочитан публичный текст",
  visual_public_screen:"Осмотрен публичный экран", live_page:"Страница открыта",
  live_entry_then_auth_boundary:"Переход к авторизации", browser_ui:"Интерфейс проверен в браузере",
  public_page_or_document:"Публичная страница или документ",
};
let countryNames;
try { countryNames = new Intl.DisplayNames(["ru"], {type:"region"}); } catch {}
const market = key => {
  if (!key) return "Рынок не указан";
  if (/^[A-Z]{2}$/.test(key) && countryNames) {
    try { return countryNames.of(key) || key; } catch {}
  }
  return key;
};
const marketLabel = key => key ? `${market(key)} · ${key}` : market(key);
const projectTitle = id => projects.get(id)?.name || routesByProject.get(id)?.[0]?.name || id;
const nf = new Intl.NumberFormat("ru-RU",{maximumFractionDigits:2});
const num = x => x === null || x === undefined || x === "" ? "—" : typeof x === "number" ? nf.format(x) : esc(x);
const SORT = new Intl.Collator("ru", {numeric:true, sensitivity:"base"});
function esc(v) {
  return String(v ?? "").replace(/[&<>"']/g,ch=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[ch]));
}
function norm(s) {
  return String(s ?? "").normalize("NFKC").toLocaleLowerCase("ru").replaceAll("ё","е").trim();
}
function text(s) { return esc(s || "—"); }
function match(haystack, words) { return !words || words.split(/\s+/).every(word => haystack.includes(word)); }
function goodUrl(raw) {
  try {
    const url = new URL(raw);
    return /^https?:$/.test(url.protocol) && !url.username && !url.password ? url.href : "";
  } catch { return ""; }
}
function urlLink(raw,label="Открыть страницу") {
  const href=goodUrl(raw);
  return href ? `<a href="${esc(href)}" target="_blank" rel="noopener noreferrer">${esc(label)} ↗</a>` : "—";
}
function urlDisplay(s) {
  return goodUrl(s) ? urlLink(s,s.replace(/^https?:\/\//,"")) : text(s);
}
function linkedUrls(raw,label) {
  return [...new Set(String(raw || "").match(/https?:\/\/[^\s|]+/g) || [])].map(u=>urlLink(u,label)).join(" · ") || "—";
}
function control(action,value,label,kind="") {
  return `<button type="button" class="btn ${kind}" data-action="${esc(action)}" data-value="${esc(value)}">${esc(label)}</button>`;
}
function entity(kind,id,label) {
  return `<button type="button" class="link-button" data-action="${esc(kind)}" data-value="${esc(id)}">${esc(label)}</button>`;
}
function badge(s,mode="") { return `<span class="pill ${mode}">${esc(s)}</span>`; }
function status(project) {
  return project.keys === 0 ? ["Совпадений нет","none"] :
    project.status === "есть интерфейсное свидетельство" ? ["Есть свидетельство",""] : ["Путь требует проверки","wait"];
}
function section(name, body) {
  return `<section class="detail-section"><h3>${esc(name)}</h3>${body}</section>`;
}
function listDetails(pairs) {
  return `<dl class="detail">${pairs.filter(([,value])=>value !== "").map(([name,value])=>`<dt>${esc(name)}</dt><dd>${value}</dd>`).join("")}</dl>`;
}
function short(s,n=48) { return s.length>n ? s.slice(0,n-1)+"…" : s; }
function title(name,subtitle) {
  return `<header class="page-title"><h1>${esc(name)}</h1><p>${esc(subtitle)}</p></header>`;
}
function select(field,label,options,selected,wide=false) {
  return `<div class="field${wide?" wide":""}"><label for="f-${esc(field)}">${esc(label)}</label><select id="f-${esc(field)}" data-filter="${esc(field)}">${options.map(([v,t]) => `<option value="${esc(v)}"${v===selected?" selected":""}>${esc(t)}</option>`).join("")}</select></div>`;
}
function numberFilter(field,label,value) {
  return `<div class="field"><label for="f-${field}">${label}</label><input type="number" inputmode="decimal" min="0" step="any" id="f-${field}" data-filter="${field}" placeholder="Любая" value="${esc(value)}"></div>`;
}
function search(value,placeholder) {
  return `<div class="field search"><label for="filter-search">Поиск</label><input type="search" id="filter-search" data-filter="words" placeholder="${esc(placeholder)}" value="${esc(value)}" autocomplete="off"></div>`;
}
function filters(body) {
  return `<div class="filters">${body}${control("reset","","Сбросить","clear")}</div><div id="results"></div>`;
}
function tabulate(headers, rows, label, numbers=[]) {
  return `<div class="table-wrap" tabindex="0" aria-label="${esc(label)}"><table><thead><tr>${headers.map((h,i)=>`<th scope="col"${numbers.includes(i)?' class="num"':""}>${esc(h)}</th>`).join("")}</tr></thead><tbody>${rows.map(row=>`<tr>${row.map((v,i)=>`<td${numbers.includes(i)?' class="num"':""}>${v}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
}
function empty(message) { return `<p class="empty">${esc(message)}</p>`; }
function hydrate(root) {
  for (const img of root.querySelectorAll("img[data-asset]:not([src])")) {
    const payload=document.getElementById("asset-"+img.dataset.asset);
    if (payload) img.src="data:image/jpeg;base64,"+payload.textContent;
  }
}
function frameButton(shot,desc,compact=false) {
  return `<button type="button" class="image-button" data-action="shot" data-value="${esc(shot.id)}" aria-label="${esc("Открыть скриншот "+desc)}"><img loading="${compact?"lazy":"eager"}" alt="${esc(desc)}" data-asset="${esc(shot.id)}"><span class="expand-mark" aria-hidden="true">⤢</span></button>`;
}
function photo(s) {
  const r=routes.get(s.route);
  return `<article class="photo">${frameButton(s,(r?.name || "Маршрут")+" · "+s.id,true)}<div class="photo-body">${entity("route",s.route,r?.name || s.route)}<p class="photo-name">${text(s.id)}</p><p>${text(s.proof)}</p></div></article>`;
}

const defaults = {
  projects:{words:"",status:"matched",page:1},
  queries:{words:"",cluster:"",level:"",market:"*",engine:"",project:"",route:"",language:"",metric:"",estimate:"",volumeMin:"",volumeMax:"",volumeSort:"",page:1},
  routes:{words:"",scope:"",project:"",shape:"",page:1},
  gallery:{words:"",project:"",route:"",page:1},
  sources:{words:"",kind:"files",region:"",page:1},
};
const state=Object.fromEntries(Object.entries(defaults).map(([key,value])=>[key,{...value}]));
const projectOptions = data.projects.filter(p=>p.keys || p.routes).map(p=>[p.id,p.name]);
for (const r of data.routes) if (!projectOptions.some(([k])=>k===r.project)) projectOptions.push([r.project,r.name || r.domain]);
projectOptions.sort((a,b)=>SORT.compare(a[1],b[1]));
const queryMarkets = [...new Set(data.queries.map(q=>q.market))].sort((a,b)=>SORT.compare(marketLabel(a),marketLabel(b)));
const queryLanguages=[...new Set(data.queries.map(q=>q.language))].sort();
const queryMetrics=[...new Set(data.queries.map(q=>q.metric).filter(Boolean))].sort();
const queryEngines = [...new Set(data.queries.map(q=>q.engine).filter(Boolean))].sort();
const sourceRegions = [...new Set(data.sources.map(s=>s.region))].sort();
const sectionNames = {overview:"Обзор",projects:"Проекты",queries:"Запросы",routes:"Маршруты",gallery:"Скриншоты",sources:"Источники"};
let current = "overview";
let searchTimer;

function overview() {
  const cards = cv.highlights || [];
  const numbers = [
    ["projects",cv.project_rows_included,"групп проектов"],
    ["queries",cv.candidate_counts.included,"поисковых ключей"],
    ["routes",cv.paths,"записей маршрутов"],
    ["gallery",cv.screenshots,"скриншотов"],
  ];
  const stats=Object.entries(cv.by_family).sort((a,b)=>b[1]-a[1]);
  const max=stats[0][1];
  return `
  <section class="hero">
    <div><p class="eyebrow">P07 · точка образовательного пути</p>
      <h1>Аналитическое сравнение образования</h1>
      <p>Рейтинги, отзывы, показатели выпускников и сравнение вариантов. От исходного запроса к результату, следующему действию и условиям оплаты.</p>
      <div class="hero-actions">${control("view","projects","Сравнить проекты","primary")}${control("view","queries","Найти запрос")}</div>
    </div>
    <aside class="hero-note"><h2>Что проверить в MainExperts</h2><p>Таблица с методикой и источниками открыта. Платная проверка имеет смысл при противоречивых данных и личных весах.</p></aside>
  </section>
  <div class="kpis">${numbers.map(([view,n,label])=>`<button type="button" class="kpi" data-action="view" data-value="${view}"><b>${num(n)}</b><span>${esc(label)}</span></button>`).join("")}</div>
  <div class="section-title"><h2>Три наблюдавшихся сценария</h2>${control("view","routes","Все маршруты","clear")}</div>
  <div class="cases">${cards.map(c=>{
    const frames=shotsByRoute.get(c.route) || [];
    const s=frames.length ? shots.get(frames[0].shot) : null;
    return `<article class="case">${s?frameButton(s,c.provider):""}<div class="case-body"><div class="eyebrow">${esc(c.provider)}</div><h3>${esc(c.title)}</h3><p>${esc(c.body)}</p>${routes.has(c.route)?entity("route",c.route,"Открыть маршрут →"):""}</div></article>`;
  }).join("")}</div>
  <div class="split">
    <section class="panel"><h2>Как ищут P07</h2>${stats.map(([k,n])=>`<button class="cluster-btn" type="button" data-action="cluster" data-value="${esc(k)}"><span class="bar-label"><span>${esc(k+" · "+labels[k])}</span><strong>${num(n)}</strong></span><span class="bar-track"><i style="width:${Math.max(2,100*n/max)}%"></i></span></button>`).join("")}</section>
    <section class="panel"><h2>Границы проверки</h2><div class="boundaries">
      <div><strong>${num(cv.project_rows_with_evidence)} из ${num(cv.project_rows_included)} групп</strong><p>Есть свидетельство хотя бы по одному экрану или маршруту. Для остальных зафиксированы ограничения.</p></div>
      <div><strong>${num(cv.by_d.D3 || 0)} подтверждённых ключей с коммерческим намерением</strong><p>Витрина с ценой показывает предложение поставщика. Покупки остаются за пределом публичной проверки.</p></div>
      <div><strong>${num(cv.included_observations)} исходных наблюдения</strong><p>Один запрос встречается в разных источниках. Частотности разных поисковиков и типов метрик показаны отдельно.</p></div>
    </div></section>
  </div>`;
}

const views = {
  projects(s) {
    return title("Проекты","Сравните, где найден спрос и чем подтверждён пользовательский путь.") +
      filters(search(s.words,"Название или домен") + select("status","Статус",[
        ["matched",num(cv.project_rows_included)+" с совпадениями"],["seen","Есть свидетельство"],["review","Путь требует проверки"],["all","Все "+num(cv.project_rows_total)+" групп"],
      ],s.status));
  },
  queries(s) {
    const locked=s.route ? `<p class="wide-note">Связано с маршрутом <strong>${esc(s.route)}</strong>. Связь установлена по адресу посадочной.</p>` : "";
    return title("Поисковые запросы","Оригинальные формулировки и оценки частотности. Для сравнения частот выберите один тип оценки, рынок и поисковик.") +
      locked + filters(search(s.words,"Например, college match quiz") +
        select("cluster","Кластер",[["","Все"],...Object.entries(labels).map(([k,v])=>[k,k+" · "+v])],s.cluster,true) +
        select("level","Доказательность",[["","Все"],...Object.entries(levels).map(([k,v])=>[k,k+" · "+v])],s.level) +
        select("market","Рынок",[["*","Все"],...queryMarkets.map(v=>[v,marketLabel(v)])],s.market) +
        select("language","Язык",[["","Все"],...queryLanguages.map(v=>[v,languages[v]||v])],s.language) +
        select("engine","Поисковик",[["","Все"],...queryEngines.map(v=>[v,v])],s.engine) +
        select("project","Проект",[["","Все"],...projectOptions.filter(([k])=>hitsByProject.has(k))],s.project,true) +
        select("metric","Тип оценки",[["","Все метрики"],...queryMetrics.map(v=>[v,metrics[v]||v])],s.metric,true) +
        select("estimate","Наличие оценки",[["","Все"],["present","Есть оценка"],["missing","Без оценки"]],s.estimate) +
        numberFilter("volumeMin","Частотность от",s.volumeMin) + numberFilter("volumeMax","Частотность до",s.volumeMax) +
        select("volumeSort","Сортировка по оценке",[["","Исходный порядок"],["desc","Сначала высокие"],["asc","Сначала низкие"]],s.volumeSort,true));
  },
  routes(s) {
    return title("Маршруты и оплата","По каждому маршруту видны публичный результат, следующее действие, цена, получатель и предел проверки.") +
      filters(search(s.words,"Проект, CTA или платный результат") +
        select("scope","Откуда взят маршрут",[["","Все"],...Object.entries(scopes)],s.scope,true) +
        select("project","Проект",[["","Все"],...projectOptions.filter(([k])=>routesByProject.has(k))],s.project,true) +
        select("shape","Доказательства",[["","Любые"],["price","Видна цена"],["shots","Есть скриншоты"]],s.shape));
  },
  gallery(s) {
    const locked=s.route ? `<p class="wide-note">Кадры маршрута <strong>${esc(s.route)}</strong>.</p>` : "";
    return title("Скриншоты","Кадры публичных экранов с привязкой к шагам. Нажмите на изображение, чтобы открыть оригинал.") +
      locked + filters(search(s.words,"Проект, ID кадра или интерфейс") +
        select("project","Проект",[["","Все"],...projectOptions.filter(([k])=>data.shots.some(x=>routes.get(x.route)?.project===k))],s.project,true));
  },
  sources(s) {
    return title("Источники","Исходные поисковые файлы и точные адреса посадочных, с которыми сопоставлены запросы.") +
      filters(search(s.words, s.kind==="files" ? "Название файла или домен" : "Домен, URL или заголовок") +
        select("kind","Реестр",[["files","Исходные выгрузки"],["pages","Посадочные страницы"]],s.kind,true) +
        select("region","Папка источника",[["","Все"],...sourceRegions.map(x=>[x,x])],s.region));
  },
};

const percentShort = value => /\d/.test(value || "") && !/не (?:показ|наблюд|указ)|неизвест|unknown/i.test(value);
function listProjects(s) {
  const w=norm(s.words);
  const found=data.projects.filter(p=>{
    const st=status(p)[1];
    const visible=s.status==="all" || (p.keys>0 && (s.status==="matched" || s.status==="seen" && st==="" || s.status==="review" && st==="wait"));
    return visible && match(norm([p.name,p.domain,p.domains].join(" ")),w);
  });
  return {
    found,
    render: rows=>tabulate(["Проект","Проверка","Ключи","Посадочные","Маршруты","Кадры"],rows.map(p=>{
      const [flag,mode]=status(p);
      return [entity("project",p.id,p.name)+`<small>${text(p.domain)}</small>`,badge(flag,mode),num(p.keys),num(p.landings),num(p.routes),num(p.shots)];
    }),"Список проектов",[2,3,4,5]),
  };
}
function listQueries(s) {
  const w=norm(s.words);
  const selectedProject=hitsByProject.get(s.project);
  const selectedRoute=hitsByRoute.get(s.route);
  const min=s.volumeMin===""?null:Number(s.volumeMin);
  const max=s.volumeMax===""?null:Number(s.volumeMax);
  const found=data.queries.filter(q=>
    (!s.cluster || q.cluster===s.cluster) &&
    (!s.level || q.level===s.level) &&
    (!s.language || q.language===s.language) &&
    (!s.metric || q.metric===s.metric) &&
    (!s.estimate || (s.estimate==="present" ? q.volume!==null : q.volume===null)) &&
    (min===null || q.volume!==null && q.volume>=min) &&
    (max===null || q.volume!==null && q.volume<=max) &&
    (s.market==="*" || q.market===s.market) &&
    (!s.engine || q.engine===s.engine) &&
    (!s.project || selectedProject?.has(q.id)) &&
    (!s.route || selectedRoute?.has(q.id)) &&
    match(querySearchIndex.get(q.id),w));
  if(s.volumeSort) found.sort((a,b)=>{
    if(a.volume===null) return b.volume===null ? 0 : 1;
    if(b.volume===null) return -1;
    return s.volumeSort==="asc" ? a.volume-b.volume : b.volume-a.volume;
  });
  return {
    found,
    render: rows=>tabulate(["Исходный запрос","Кластер и намерение","Рынок","Поиск","Оценка"],rows.map(q=>[
      entity("query",q.id,q.raw)+`<small>${text(languages[q.language] || q.language)} · ${num(obsByQuery.get(q.id)?.length || 0)} наблюд.</small>`,
      badge(q.level,q.level==="D3"?"wait":"")+ ` <span>${text(q.cluster)}</span><small>${text(intents[q.intent] || q.intent)}</small>`,
      text(market(q.market)),text(q.engine),num(q.volume)+ `<small>${text(metrics[q.metric] || q.metric)}</small>`,
    ]),"Реестр запросов",[4]),
  };
}
function listRoutes(s) {
  const w=norm(s.words);
  const found=data.routes.filter(r=>
    (!s.scope || r.scope===s.scope) &&
    (!s.project || r.project===s.project) &&
    (!s.shape || s.shape==="shots" && shotsByRoute.has(r.id) || s.shape==="price" && percentShort(r.price)) &&
    match(norm([r.name,r.domain,r.id,r.cta,r.translation,r.outcome,outcomes[r.outcome],r.free,r.paid,r.price].join(" ")),w));
  return {
    found,
    render: rows=>tabulate(["Проект и маршрут","Источник маршрута","Что наблюдалось","Текст действия","Цена"],rows.map(r=>[
      entity("route",r.id,r.name || r.domain)+`<small>${text(r.id)}${shotsByRoute.has(r.id)?" · "+num(shotsByRoute.get(r.id).length)+" кадров":""}</small>`,
      badge(scopes[r.scope] || r.scope,r.scope==="external_benchmark"?"wait":"none"),
      text(outcomes[r.outcome] || r.outcome),text(short(r.cta || "—",100)),text(r.price),
    ]),"Таблица маршрутов"),
  };
}
function listGallery(s) {
  const w=norm(s.words);
  const allowed=s.route ? new Set((shotsByRoute.get(s.route) || []).map(x=>x.shot)) : null;
  const found=data.shots.filter(x=>{
    const route=routes.get(x.route);
    return (!s.route || allowed.has(x.id)) && (!s.project || route?.project===s.project) &&
      match(norm([x.id,x.proof,route?.name,route?.domain,x.route].join(" ")),w);
  });
  return {found, perPage:18, render: rows=>`<div class="gallery">${rows.map(photo).join("")}</div>`};
}
function listSources(s) {
  const w=norm(s.words);
  if (s.kind==="pages") {
    const found=data.landings.filter(l=>
      (!s.project || l.project===s.project) && (!s.region || l.regions.split("|").includes(s.region)) &&
      match(norm([l.domain,l.url,l.title,l.roleNote,projectTitle(l.project),l.roles,feedStates[l.status]].join(" ")),w));
    return {found,render: rows=>tabulate(["Исходный адрес","Проект","Ключи","Проверка","Контекст"],rows.map(l=>[
      l.url ? urlLink(l.url,short(l.url,99)) : "Адрес отсутствует",
      projects.has(l.project)?entity("project",l.project,projectTitle(l.project)):text(projectTitle(l.project)),
      num(l.keys),text(feedStates[l.status] || l.status),text(l.roleNote || l.note),
    ]),"Посадочные страницы",[2])};
  }
  const found=data.sources.filter(x=>
    (!s.region || x.region===s.region) && match(norm([x.name,x.domain,x.id].join(" ")),w));
  return {found,render: rows=>tabulate(["Файл","Папка","Строки","Ключи P07","Наблюдения P07"],rows.map(x=>[
    urlLink(x.url,x.name)+`<small>${text(x.domain)}${x.incomplete==="true"?" · признак усечения":""}</small>`,
    text(x.region),num(x.rows),num(x.keys),num(x.included),
  ]),"Источники",[2,3,4])};
}
const listing={projects:listProjects,queries:listQueries,routes:listRoutes,gallery:listGallery,sources:listSources};

function updateResults() {
  const box=document.getElementById("results");
  if (!box || !listing[current]) return;
  const active=state[current];
  const {found,render,perPage=28}=listing[current](active);
  const totalPages=Math.max(1,Math.ceil(found.length/perPage));
  active.page=Math.max(1,Math.min(totalPages,active.page));
  const start=(active.page-1)*perPage;
  let html=`<div class="results-head"><span role="status" aria-live="polite">${found.length ? "Совпадений · "+num(found.length) : "Совпадений · 0"}</span>${found.length?`<span>${num(start+1)}–${num(Math.min(start+perPage,found.length))}</span>`:""}</div>`;
  if (!found.length && current==="queries" && active.volumeMin!=="" && active.volumeMax!=="" && Number(active.volumeMin)>Number(active.volumeMax)) {
    html+=empty("Минимальная частотность должна быть не выше максимальной.");
  } else if (!found.length) html+=empty("По этим условиям совпадений нет. Измените запрос или сбросьте фильтры.");
  else html+=render(found.slice(start,start+perPage));
  if (totalPages>1) {
    const pageButton=(delta,label,disabled)=>`<button class="btn" type="button" data-action="page" data-value="${delta}" ${disabled?"disabled":""}>${label}</button>`;
    html+=`<div class="pager" aria-label="Страницы результатов">${pageButton(-1,"Назад",active.page===1)}<span>Страница ${num(active.page)} из ${num(totalPages)}</span>${pageButton(1,"Дальше",active.page===totalPages)}</div>`;
  }
  box.innerHTML=html;
  hydrate(box);
}

function show(view,top=true) {
  if (!Object.hasOwn(sectionNames,view)) view="overview";
  clearTimeout(searchTimer);
  current=view;
  for (const a of document.querySelectorAll("[data-tab]")) {
    if (a.dataset.tab===view) a.setAttribute("aria-current","page");
    else a.removeAttribute("aria-current");
  }
  document.title=sectionNames[view]+" · MainExperts P07";
  app.innerHTML=view==="overview"?overview():views[view](state[view]);
  if (view==="overview") hydrate(app);
  else updateResults();
  if (top) window.scrollTo(0,0);
}
function navigate(view,parts,focus=false) {
  if (!Object.hasOwn(sectionNames,view)) return;
  if (parts && state[view]) state[view]={...defaults[view],...parts};
  if (detail.open) detail.close();
  if (lightbox.open) lightbox.close();
  if (location.hash!=="#"+view) {
    try { history.pushState(null,"","#"+view); }
    catch { location.hash="#"+view; }
  }
  show(view);
  if (focus) {
    const title=app.querySelector("h1");
    if (title) { title.tabIndex=-1; title.focus({preventScroll:true}); }
  }
}
function dialogContent(kicker,name,markup) {
  document.getElementById("detail-kicker").textContent=kicker;
  document.getElementById("detail-title").textContent=name;
  const body=document.getElementById("detail-body");
  body.innerHTML=markup;
  hydrate(body);
  if (!detail.open) detail.showModal();
  detail.scrollTop=0;
  detail.querySelector("[data-close]").focus({preventScroll:true});
}
function metricTiles(stats) {
  return `<div class="detail-top">${stats.map(([v,name])=>`<div><strong>${num(v)}</strong>${esc(name)}</div>`).join("")}</div>`;
}
function routeRows(list) {
  return list.length ? `<div class="routelist">${list.map(r=>`<button type="button" data-action="route" data-value="${esc(r.id)}"><strong>${text(r.id)}</strong> · ${text(outcomes[r.outcome] || r.outcome)}${r.cta?" · "+text(short(r.cta,95)):""}</button>`).join("")}</div>`
    : empty("Связанных маршрутов в реестре нет.");
}
function openProject(id) {
  const p=projects.get(id);
  if (!p) return;
  const rr=routesByProject.get(id) || [];
  const qq=hitsByProject.get(id) || new Set();
  const pages=(landingsByProject.get(id) || []).filter(x=>x.url && x.keys>0);
  const counts = new Map();
  for (const qid of qq) {
    const q=queries.get(qid);
    if (q) counts.set(q.cluster,(counts.get(q.cluster) || 0) + 1);
  }
  const top=[...counts.entries()].sort((a,b)=>b[1]-a[1]);
  const tags=top.length ? tabulate(["Кластер","Ключи"],top.map(([k,n])=>[
    `<button class="link-button" data-action="project-cluster" data-value="${esc(id)}" data-cluster="${esc(k)}">${text(k+" · "+(labels[k]||k))}</button>`,num(n),
  ]),"Кластеры проекта",[1]) : empty("В корпусе у этой группы нет принятых ключей P07.");
  const [st,mode]=status(p);
  dialogContent("Проект · "+p.domain,p.name,
    metricTiles([[p.keys,"поисковых ключей"],[p.observations,"наблюдений"],[p.landings,"посадочных"],[p.shots,"скриншотов"]]) +
    `<div class="actions">${badge(st,mode)}${p.keys ? control("project-queries",id,"Все запросы","primary") : ""}${rr.length?control("project-routes",id,"Все маршруты"):""}${pages.length?control("project-pages",id,"Посадочные"):""}</div>` +
    section("Кластеры проекта",tags) + section("Маршруты и пределы проверки",routeRows(rr)) +
    section("Частые посадочные",pages.length ? tabulate(["Адрес","Ключи","Публичная проверка"],pages.slice(0,8).map(l=>[
      urlLink(l.url,short(l.url,95)),num(l.keys),text(feedStates[l.status] || l.status),
    ]),"Примеры посадочных проекта",[1]) : empty("Пригодных адресов для принятых ключей в этой группе нет.")));
}
function openQuery(id) {
  const q=queries.get(id);
  if (!q) return;
  const obs=obsByQuery.get(id) || [];
  const linked=[...new Set((linksByQuery.get(id) || []).map(x=>x.route))].map(i=>routes.get(i)).filter(Boolean);
  const headings=listDetails([
    ["Кластер",entity("cluster",q.cluster,q.cluster+" · "+(labels[q.cluster]||""))],
    ["Намерение",text(q.intent+" · "+(intents[q.intent]||""))],["Рынок",text(marketLabel(q.market))],
    ["Поисковик",text(q.engine)],["Язык",text(languages[q.language] || q.language)],
    ["Оценка частоты",num(q.volume)+" · "+text(metrics[q.metric] || q.metric)],
    ["Уровень",badge(q.level,q.level==="D3"?"wait":"")+" "+text(levels[q.level])],
    ["Основание разметки",text(q.reason)],
  ]);
  const list=tabulate(["Проект и оригинал","Наблюдение","Посадочная","Частота","Исходник"],obs.map(o=>{
    const src=sources.get(o.source);
    const details=[o.sheet,o.row ? "строка "+num(o.row) : "",o.date].filter(Boolean).join(" · ");
    const pt=projects.has(o.project)?entity("project",o.project,projectTitle(o.project)):text(projectTitle(o.project));
    return [pt+`<small>${text(o.raw)}</small>`,text(o.engine)+" · "+text(market(o.market))+`<small>${text(details)}</small>`,
      urlLink(o.target,short(o.target,75)),num(o.volume)+`<small>${text(metrics[o.metric] || o.metric)}</small>`,urlLink(src?.url,"Файл")];
  }),"Все исходные наблюдения запроса",[3]);
  dialogContent("Запрос · "+q.level,q.raw,headings+section("Исходные наблюдения · "+num(obs.length),list)+section("Маршруты, связанные по адресу · "+num(linked.length),routeRows(linked)));
}
function openRoute(id) {
  const r=routes.get(id);
  if (!r) return;
  const stepRows=stepsByRoute.get(id) || [];
  const shotRows=[...new Set((shotsByRoute.get(id) || []).map(x=>x.shot))].map(k=>shots.get(k)).filter(Boolean);
  const qcount=hitsByRoute.get(id)?.size || 0;
  const detailsMarkup=listDetails([
    ["Тип",badge(scopes[r.scope] || r.scope,r.scope==="external_benchmark"?"wait":"")],
    ["Исходная посадочная",urlDisplay(r.entry)],["Последний доступный адрес",urlDisplay(r.final)],
    ["Текст действия",text(r.cta)+(r.translation?" · "+text(r.translation):"")],
    ["Открытый результат",text(r.free)],["Следующий или платный результат",text(r.paid || outcomes[r.outcome] || r.outcome)],
    ["Видимая цена",text(r.price)],["Исполнитель на странице",text(r.provider)],
    ["Подтверждённый получатель оплаты",text(r.recipient || "Получатель не наблюдался")],
    ["Ограничение",text(r.limits || r.access)],["Проверка",text(verification[r.verification] || r.verification)],
    ["Источники",linkedUrls(r.sources,"Источник")],
  ]);
  const timeline=stepRows.length ? `<ol class="timeline">${stepRows.map((s,index)=>`<li><h4>${num(index+1)}. ${text(s.element || "Публичный экран")}</h4>
    ${s.cta?`<p><strong>${text(s.cta)}</strong></p>`:""}${s.outcome?`<p>${text(s.outcome)}</p>`:""}${s.next?`<p>${urlDisplay(s.next)}</p>`:""}${goodUrl(s.url)?urlLink(s.url,"Страница"):""}</li>`).join("")}</ol>` : empty("Пошаговое наблюдение недоступно.");
  dialogContent("Маршрут · "+r.id,r.name || r.domain,
    detailsMarkup + `<div class="actions">${projects.has(r.project)?control("project",r.project,"Карточка проекта"):""}${qcount ? control("route-queries",r.id,"Связанные запросы · "+num(qcount),"primary"):""}</div>` +
    section("Шаги",timeline) + section("Скриншоты · "+num(shotRows.length),
      shotRows.length ? `<div class="gallery">${shotRows.map(photo).join("")}</div>` : empty("В реестре есть описание или ограничение, кадр недоступен.")));
}
function openShot(id) {
  const s=shots.get(id);
  if (!s) return;
  const r=routes.get(s.route);
  const label=(r?.name || "Публичный интерфейс")+" · "+s.id;
  document.getElementById("shot-title").textContent=label;
  const body=document.getElementById("shot-body");
  body.innerHTML=`<div class="shot-canvas" id="shot-canvas"><img alt="${esc(label)}" data-asset="${esc(id)}"></div>
    <p class="shot-caption">${text(s.proof)} · ${text(s.size)} · ${text(s.date?.slice(0,10))}</p>
    <div class="actions">${control("zoom","","Масштаб 1:1")}<a class="btn" id="shot-download" download="${esc(id)}.jpg">Скачать JPEG</a>${urlLink(s.url,"Источник")}${control("shot-route",s.route,"Карточка маршрута")}</div>`;
  hydrate(body);
  const download=body.querySelector("#shot-download");
  download.href=body.querySelector("img").src;
  if (!lightbox.open) lightbox.showModal();
  lightbox.scrollTop=0;
  lightbox.querySelector("[data-close]").focus({preventScroll:true});
}

const handlers={
  view: (v)=>navigate(v,undefined,true),
  project: openProject, query:openQuery,route:openRoute,shot:openShot,
  cluster: v=>navigate("queries",{cluster:v},true),
  "project-cluster": (v,b)=>navigate("queries",{project:v,cluster:b.dataset.cluster},true),
  "project-queries": v=>navigate("queries",{project:v},true),
  "project-routes": v=>navigate("routes",{project:v},true),
  "project-pages": v=>navigate("sources",{kind:"pages",project:v},true),
  "route-queries": v=>navigate("queries",{route:v},true),
  "shot-route": v=>{lightbox.close();openRoute(v);},
  reset: ()=>{state[current]={...defaults[current]};show(current,false);app.querySelector("input")?.focus();},
  page: v=>{
    state[current].page+=Number(v);
    updateResults();
    const r=document.querySelector(".results-head");
    r?.scrollIntoView({block:"nearest",behavior:"instant"});
    if (r) {r.tabIndex=-1;r.focus({preventScroll:true});}
  },
  zoom: (_,b)=>{
    const active=document.getElementById("shot-canvas").classList.toggle("original");
    b.textContent=active?"Уместить в экран":"Масштаб 1:1";
    b.setAttribute("aria-pressed",String(active));
  },
};
document.addEventListener("click", e=>{
  const button=e.target.closest("[data-action]");
  if (button) { handlers[button.dataset.action]?.(button.dataset.value,button);return; }
  const nav=e.target.closest("[data-tab],.brand");
  if (nav) { e.preventDefault(); navigate(nav.dataset.tab||"overview",undefined,true);return; }
  const close=e.target.closest("[data-close]");
  if (close) document.getElementById(close.dataset.close)?.close();
});
app.addEventListener("input",e=>{
  const field=e.target.dataset.filter;
  if (field!=="words" && field!=="volumeMin" && field!=="volumeMax" || !state[current]) return;
  if (e.target.type==="number" && !e.target.validity.valid) return;
  state[current][field]=e.target.value;
  state[current].page=1;
  clearTimeout(searchTimer);
  searchTimer=setTimeout(updateResults,110);
});
app.addEventListener("change",e=>{
  const field=e.target.dataset.filter;
  if (!field || field==="words" || !state[current] || e.target.type==="number" && !e.target.validity.valid) return;
  state[current][field]=e.target.value;
  state[current].page=1;
  if (field==="kind") {
    state[current].project="";
    show(current,false);
    app.querySelector("#f-kind")?.focus();
  } else updateResults();
});
for (const dialog of [detail,lightbox]) {
  dialog.addEventListener("click", e=>{if (e.target===dialog) dialog.close();});
}
function hashView() {
  const target=location.hash.slice(1);
  if (target && target!=="main" && Object.hasOwn(sectionNames,target)) show(target);
  else if (!target) show("overview");
}
window.addEventListener("hashchange", hashView);
window.addEventListener("popstate",hashView);
show(Object.hasOwn(sectionNames,location.hash.slice(1))?location.hash.slice(1):"overview");

})().catch(error=>{document.getElementById("app").textContent="Не удалось открыть данные. Откройте файл в актуальном браузере с поддержкой распаковки gzip.";console.error(error);});
