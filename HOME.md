---
type: home
title: MainExperts — дом хранилища (Obsidian)
updated: 2026-07-13
---

# 🏠 MainExperts — память и знания (Obsidian vault)

Этот репозиторий открывается как **хранилище Obsidian**: открой корневую папку в Obsidian
(«Open folder as vault»), синхронизация — через git. Эта заметка — точка входа; полная карта
содержания — [[MOC]].

## ▶️ Первый запуск (1 минута)

1. Получи папку репозитория одним из способов:
   - **Проще всего (без git):** GitHub → ветка `claude/mainexperts-docs-architecture-pm08hn`
     → кнопка **Code → Download ZIP** → распакуй.
   - **С git (для синхронизации):**
     `git clone -b claude/mainexperts-docs-architecture-pm08hn https://github.com/logist888/max.git mainexperts`
   - **GitHub Desktop:** Clone → выбрать репозиторий → сверху переключить branch на
     `claude/mainexperts-docs-architecture-pm08hn`.
2. Obsidian → **Open folder as vault** → выбери эту папку. На вопрос про доверие плагинам —
   можно оставить core-плагины (community не требуются).
3. Слева в панели **«Закладки»** уже есть 🏠 HOME · 🗺 MOC · 🧠 memory · 📄 DMS — начни оттуда.
4. Синхронизация: `git pull` (забрать мои правки) / `git commit && git push` (отправить свои).
   По желанию — community-плагин **Obsidian Git** для авто-синхронизации без терминала.

> Живого коннектора Obsidian у ассистента нет (Obsidian — локальное приложение, облачного API
> для подключения нет). «Подключение» работает так: ассистент пишет память как Obsidian-заметки
> (frontmatter + вики-ссылки) прямо в этот репозиторий, ты открываешь папку в Obsidian, git
> переносит изменения. См. `SYSTEM.md`, раздел «Obsidian».

## 🧠 Память

- [[memory/memory|memory]] — **дословный снимок канонической памяти** с Google Drive (эталон,
  `memory/memory.md`; не путать с реконструкцией `reference/memory.md`).
- [[MOC]] — карта содержания хранилища (точка входа, `vault/00-index/MOC.md`).
- [[tags]] — контролируемый словарь меток (`vault/00-index/tags.md`).
- Рабочие заметки: `vault/10-sources/` (источники), `vault/20-notes/` (атомарные мысли),
  `vault/30-entities/` (сущности), `vault/40-reports/` (черновики).

Якоря: [[potok-1-hnw]] · [[potok-2-voronka]] · [[gipoteza-skrininga]].

## 📚 Канон знаний (docs/)

- [[01-strategy]] · [[02-product]] · [[03-audience-custdev]] · [[04-operations]] ·
  [[05-risk-compliance]] · [[06-data-tools-payments]] · [[07-principles-open-questions]]
- Борды MMS: [[08-board-system]] → модуль `docs/boards/`.
- [[09-system-map]] · [[10-data-model]] · [[11-gtm-strategy]] · [[12-traffic-platform-decisions]]
- Система документации: [[13-document-system]] → модуль `docs/dms/` (реестр, карточки, матрицы,
  деревья, роадмап, governance); материализованные документы — `docs/dms/documents/`.

## ⚙️ Как это работает

- **Хранилище** — весь репозиторий; шумные папки (`scripts/`, `raw/`, `*.html`) скрыты фильтром
  Obsidian (`.obsidian/app.json`).
- **Шаблоны заметок** — `vault/_templates/` (source/note/entity/report), подключены в
  настройках Templates.
- **Правила** — `CLAUDE.md` (протокол), `SYSTEM.md` (устройство), скиллы `boot`/`ingest`/`report`.
- **Синхронизация** — git (`git pull`/`push`). Обсидиан-служебные файлы (`workspace*.json`,
  кэш) в git не идут.

## Связи

- Карта содержания: [[MOC]] · Устройство системы: `SYSTEM.md` · Протокол: `CLAUDE.md`.
