# Промпты для фото на лендинг

Три кадра под слоты в `web/index.html`. Все — **без текста и логотипов**, люди **обезличены**
(со спины / не в фокусе / не узнаваемы), премиальная нейтральная палитра с лёгким синим акцентом
в духе Apple.

**Модель:** ChatGPT Image (GPT Image 2) — вы генерируете в ChatGPT, текст в кадре не нужен, лица
не важны. Если есть доступ к **Nano Banana Pro** — там кожа/свет чуть лучше, промпты подойдут те же
(уберите строку `quality: high`).

**Формат:** генерируйте в **горизонтальной (landscape)** ориентации. На странице кадры обрезаются
по месту (`object-fit: cover`): слот 1 — под 16:9, слоты 2–3 — под широкую полосу. Широкого
горизонтального кадра достаточно для всех трёх.

---

## Слот 1 — Hero (16:9): «понятный путь к профессии и магистратуре за рубежом»

```
A calm, premium editorial photograph, wide landscape orientation. A single young person around 20 years old, seen from behind in soft silhouette, standing in a bright airy modern university atrium with tall floor-to-ceiling windows, pale wood floor and white walls. They look out toward a luminous horizon with a softly blurred international campus and a clear pale-blue morning sky. Vast negative space, minimalist composition, the figure placed on the left third. Soft diffused natural daylight from the windows, gentle cool-blue tones balanced with warm neutral wood, no harsh shadows. Shot on Sony A7IV, 35mm f/2, shallow depth of field, natural skin and fabric texture, understated editorial premium look, clean Apple-like aesthetic. The person is anonymous and not identifiable. Do not include any text, letters, logos or watermarks. quality: high
```

**Структура:** молодой человек со спины у панорамного окна светлого кампуса, смотрит на горизонт →
метафора пути. Много воздуха, фигура в левой трети. Мягкий дневной свет, нейтрально + холодный синий
акцент. Снято на 35mm, editorial, премиум, без лиц и текста.

---

## Слот 2 — Полоса: «магистратура за рубежом» (кампус / библиотека)

```
A bright spacious modern university library, wide landscape orientation. Warm light-wood shelves and white minimalist architecture, tall windows with soft daylight. A student seen from a distance and from behind walks slowly through the aisle carrying a bag, unidentifiable. Large areas of calm negative space, clean lines, neutral palette of white, pale oak and a subtle cool-blue reflection from the windows. Soft diffused natural light, airy and quiet atmosphere. Shot on Sony A7IV, 35mm f/2.8, natural textures, editorial premium look, clean Apple-like aesthetic. Do not include any text, letters, logos or watermarks. quality: high
```

**Структура:** светлая современная библиотека/кампус, студент вдалеке со спины, много воздуха,
нейтральное дерево + белый + лёгкий синий отблеск. Тихая премиальная атмосфера, без лиц и текста.

---

## Слот 3 — Полоса: «встреча-наставничество / разбор с экспертом»

```
A warm understated mentoring moment, wide landscape orientation. Two people sit at a light oak table in a bright minimalist room, an over-the-shoulder view where faces are not identifiable and softly out of focus. On the table an open laptop with a soft blue screen glow, a notebook and a cup of coffee. One person gestures gently while explaining. Calm neutral palette of white, pale wood and one subtle blue accent from the screen, generous negative space on the right. Soft diffused window light from the left, natural skin and fabric texture, no harsh shadows. Shot on Sony A7IV, 50mm f/2, shallow depth of field, editorial premium look, clean Apple-like aesthetic. People are anonymous and not identifiable. Do not include any text, letters, logos or watermarks. quality: high
```

**Структура:** двое за светлым столом, вид из-за плеча (лица не читаются), ноутбук с мягким синим
свечением, разговор-наставничество. Нейтрально + один синий акцент, воздух справа. Мягкий боковой
свет, премиум, без узнаваемых лиц и текста.

---

## Как вставить готовые фото

Самый простой путь — **пришлите картинки мне в чат**, я вставлю их в нужные слоты (перекодирую в
base64 и заменю SVG-плейсхолдеры), страница останется одним самодостаточным файлом.

Если хотите вставить сами:
1. В `web/index.html` найдите комментарий `ФОТО-СЛОТ N`.
2. Внутри `<div class="hero-media …">` (слот 1) или `<div class="photo-band …">` (слоты 2–3)
   удалите тег `<svg>…</svg>` и вставьте `<img src="data:image/jpeg;base64,ВАШ_BASE64" alt="">`.
3. Base64 получите командой: `base64 -w0 фото.jpg` — вставьте результат вместо `ВАШ_BASE64`.

Совет: не увлекайтесь тяжёлыми фото — ужмите каждое до ~150–250 КБ (ширина ~1600px, JPEG качество
~80), иначе страница разрастётся. Плейсхолдеры-градиенты выглядят аккуратно и сами по себе, так что
можно добавлять фото по одному.
