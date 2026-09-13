---
type: index
title: MOC — карта содержания MainExperts
updated: 2026-06-23
---

# Карта содержания (MOC)

Точка входа в хранилище. Грузить после `CLAUDE.md`.

## Канон знаний — docs/ (правится осознанно, через ingest шаг 7)
- `docs/01-strategy.md` — проект, цели, монетизация, два потока, гипотеза скрининга.
- `docs/02-product.md` — продукт, цифровой профиль, квиз, флоу, тех-состояние, блокеры.
- `docs/03-audience-custdev.md` — четыре персонажа, custdev семей и экспертов.
- `docs/04-operations.md` — три слоя карты, CJM, V4.1, Федоренко, узкое место.
- `docs/05-risk-compliance.md` — путь риска, регулятор, данные несовершеннолетних, лицензии.
- `docs/06-data-tools-payments.md` — базы профессий, трафик, аналитика, платежи, инструменты.
- `docs/07-principles-open-questions.md` — принципы, открытые вопросы, горизонт, артефакты.
- `docs/15-partner-network-tz.md` — ТЗ на первый запуск партнёрской сети (правки 13.09.2026): сущности, правила, состояния, экраны, расчёты по доле партнёра, материалы, приёмка, открытые решения, красная команда, разбор Д01–Д17. Промпт: `docs/prompts/partner-network-tz.md`. PDF: [[../40-reports/2026-09-13-partnerskaya-set-tz.pdf]].
- `docs/17-partner-network-brief.md` — краткий ввод в партнёрскую сеть для разработчика: модель, правила, порядок работ, блокеры. PDF: [[../40-reports/2026-09-13-partnerka-brief-razrabotchiku.pdf]].
- `docs/16-partner-flows-tz.md` — ТЗ по путям семьи и партнёра для разработчиков (правки 13.09.2026): шаги, экраны, запросы, правила, состояния, приёмка. Интерактивная карта — `docs/html/partner-flows.html`, прототип кабинета партнёра — `docs/html/partner-cabinet.html`. Поэкранные PDF для телефона: [[../40-reports/2026-09-13-puti-semi-partnera-ekrany.pdf]] · [[../40-reports/2026-09-13-kabinet-partnera-ekrany.pdf]]. PDF: [[../40-reports/2026-09-13-partnerskaya-set-tz-puti.pdf]].
- `docs/14-partner-network.md` — партнёрская сеть, «Партнёрская розница» (актуально на 13.09.2026): решения команды со статусами, три конструкции расчёта и выбранная доля партнёра 35 %, слои цены, значения для России, роли, сценарный анализ, пути партнёра и семьи, учёт и право, план первого запуска, находки, вопросы. PDF: [[../40-reports/2026-09-13-partnerskaya-set-kanon.pdf]]. Источники: [[../10-sources/2026-09-13-pravki-komandy-partnerka]] ·  [[../10-sources/2026-09-08-sozvon-partnerskaya-set]] · [[../10-sources/2026-09-08-partner-network-strategy-pdf]] · [[../10-sources/2026-09-09-partnerskaya-delta-v3-chatgpt]] · [[../10-sources/2026-09-09-sozvon-partnerskaya-set-2]].
- `docs/private/stream-1-hnw.md` — поток-1, HNW. **Конфиденциально, в git не идёт, без явной причины не открывать.**

Дословный снимок Диска — `memory/memory.md`. Оригиналы методологий — `reference/`.

## Рабочие заметки — vault/ (из новых ингестов)
Якоря потоков и гипотезы:
- [[../30-entities/potok-1-hnw]] · [[../30-entities/potok-2-voronka]] · [[../30-entities/gipoteza-skrininga]]

Источники — `vault/10-sources/`; атомарные заметки — `vault/20-notes/`;
сущности (персонажи ЦА, концепции, профессии) — `vault/30-entities/`;
черновики отчётов — `vault/40-reports/`.

## Открытые проверки
- заметки со `status: требует-проверки`: `rg "требует-проверки" vault/`
- открытые вопросы канона — `docs/07-principles-open-questions.md`.
