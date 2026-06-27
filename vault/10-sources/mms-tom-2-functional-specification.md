---
id: src-mms-tom-2
type: source
title: MMS. Том II. Functional Specification
created: 2026-06-27
updated: 2026-06-27
stream: общее
source_ref: "MainExperts Management System (MMS). Том II. Functional Specification. Версия 1.0"
source_date: 2026-06-27
source_url: "https://drive.google.com/file/d/1h1CcYekcsDG3SXX1zIKR_ZL0JkHwn8uD/view"
pages: "Объявлено XIV разделов; извлечено ~49 100 знаков — главы 1–10 (Product оборван на §10.11). Разделы IV–XIV (Data Dictionary, ETL, Security, AI Copilot, Administration, Reporting, Notifications, Integrations, NFR, Acceptance) в извлечённом тексте отсутствуют."
tags: [управление, метрики, борды, kpi, дашборд]
links: ["[[mms-tom-1-business-architecture]]", "[[../../docs/08-board-system]]"]
---

## Конспект

Функциональная спецификация информационной системы, реализующей философию Тома I.
Основной документ для Product Owner, аналитиков, архитектора, backend/frontend, BI, Data
Engineers, QA, DevOps, AI-команды. Заявленная структура — XIV разделов; раздел III
**«Управленческие борды»** и есть система бордов: единый Dashboard Framework (Header / KPI
Cards / Trends / Alerts / Drill Down / Actions; принципы SSOT / Event-Driven / KPI-Driven
/ Decision-Driven / AI-First; иерархия L0–L3) и семь дашбордов — **Owner, Finance,
Marketing, Sales, Operations, Expert Network, Product**. Каждый борд описан единообразно:
назначение (вопросы), структура экрана, KPI-карточки, drill-down-деревья, alerts→playbook,
AI Explain, фильтры, требования производительности (≤2 сек загрузка, ≤1 сек drill-down,
≤5 сек AI/forecast), критерии приёмки. **Это видение/функциональные требования, не
детальное ТЗ:** многие KPI даны без формул и порогов (формулы — предмет Тома I и Data
Dictionary, который в извлечении отсутствует).

## Карта разделов

Объявленная структура (Предисловие): I Общие требования · II Пользователи и роли ·
III Управленческие борды · IV KPI Framework · V Data Dictionary · VI ETL Architecture ·
VII Security · VIII AI Copilot · IX Administration · X Reporting · XI Notifications ·
XII Integrations · XIII Non-Functional Requirements · XIV Acceptance Criteria.

Извлечённые главы:
- Гл. 1 Общие требования — цель, задачи, принципы проектирования, слоистая архитектура (Events→Raw→Objects→KPI→Dashboards→AI→Decisions).
- Гл. 2 Пользователи — RBAC, роли (Owner/CEO/CFO/COO/CMO/CTO/Product Owner/Expert/Analyst/Support), матрица доступа, авторизация, сессии.
- Гл. 3 Dashboard Framework — единые элементы борда, иерархия L0–L3, KPI Card, правила Drill Down / Alerts / AI Explain.
- Гл. 4 Owner Dashboard — 9 зон (AI Morning Brief, Strategic KPI, Financial Health, Growth, Operations, AI, Critical Alerts, Decision Queue, Forecast, Active Initiatives).
- Гл. 5 Finance Dashboard — P&L, Cash Flow, Balance Sheet, Runway, Contribution, Unit Economics, Forecast, Scenario Modeling.
- Гл. 6 Marketing Dashboard — воронка, каналы, кампании, DRR/CAC/LTV/ROMI, когорты, атрибуция, AI-рекомендации.
- Гл. 7 Sales Dashboard — Pipeline, Funnel, Forecast, менеджеры, причины проигрышей, Velocity, сегментация, AI Copilot.
- Гл. 8 Operations Dashboard — Capacity, Utilization, очередь, SLA, распределение нагрузки, Hiring Forecast, AI Capacity.
- Гл. 9 Expert Network Dashboard — карточка эксперта, Performance Score, рейтинг, удовлетворённость, развитие, матрица эффективности.
- Гл. 10 Product Dashboard — портфель, матрица продуктов, карточка продукта, Contribution, жизненный цикл, adoption. **Оборван на §10.11; AI Product Insights / Product Alerts / Drill Down / критерии приёмки — отсутствуют.**

## Извлечённые заметки

Источник всего модуля `docs/boards/` (00–16, 90) и обзора `docs/08-board-system.md`.
Пробел: при появлении полного Тома II (разделы IV–XIV) — дополнить `01-kpi-framework`,
`90-acceptance` и завести файлы по Data Dictionary / ETL / Security / Integrations.
