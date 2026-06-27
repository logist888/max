# CHANGELOG контекста MainExperts

## 2026-06-27 — система управленческих бордов (MMS)
Из двух документов Google Drive — MMS Том I «Business Architecture» и Том II «Functional
Specification» (`1.pdf`, `2.pdf`) — собран модуль канона `docs/boards/` и обзор
`docs/08-board-system.md`: каркас борда, KPI-фреймворк (L0–L3), роли/доступ, цикл решений и
playbooks, семь бордов (Owner, Finance, Marketing, Sales, Operations, Expert Network,
Product), сводные критерии приёмки. Провенанс — в `vault/10-sources/`. Известный пробел:
извлечение Тома II оборвано на §10.11; разделы IV–XIV (Data Dictionary, ETL, Security, NFR,
Acceptance и др.) недоступны и помечены пробелом, не достроены. Обзор содержит критический
разбор разрыва между амбицией MMS и текущей стадией проекта.

## 2026-06-23 — начальный снимок
Первая выгрузка контекста проекта для переноса в Claude Code.
Источник истины остаётся в Claude.ai (память проекта плюс Google Drive).
При существенных изменениях (вебинар, блокеры, статусы) пересобрать комплект тем же промптом в Claude.ai и заменить файлы.
