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
- `docs/08-board-system.md` — система управленческих бордов MMS (обзор, иерархия L0–L3, критика); канон — `docs/boards/`.
- `docs/boards/` — каркас борда, KPI-фреймворк (L0–L3), роли/доступ, цикл решений, стартовый контур S0–S2 (`04-stage0-mvp`), семь бордов (Owner…Product), критерии приёмки.
- `docs/09-system-map.md` — блок-схема системы: листы и процессы (Mermaid, рендер на GitHub).
- `docs/10-data-model.md` — реляционная модель запуска продуктов (ядро + слой целей + факты), ER-схема, демо-данные, витрины, приёмка; закрывает пробел Data Dictionary.
- `docs/private/stream-1-hnw.md` — поток-1, HNW. **Конфиденциально, в git не идёт, без явной причины не открывать.**

Дословный снимок Диска — `memory/memory.md`. Оригиналы методологий — `reference/`.
Источники MMS — `vault/10-sources/mms-tom-1-business-architecture.md`, `…/mms-tom-2-functional-specification.md`.

## Рабочие заметки — vault/ (из новых ингестов)
Якоря потоков и гипотезы:
- [[../30-entities/potok-1-hnw]] · [[../30-entities/potok-2-voronka]] · [[../30-entities/gipoteza-skrininga]]

Источники — `vault/10-sources/`; атомарные заметки — `vault/20-notes/`;
сущности (персонажи ЦА, концепции, профессии) — `vault/30-entities/`;
черновики отчётов — `vault/40-reports/`.

## Открытые проверки
- заметки со `status: требует-проверки`: `rg "требует-проверки" vault/`
- открытые вопросы канона — `docs/07-principles-open-questions.md`.
