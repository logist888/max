# CHANGELOG контекста MainExperts

## 2026-06-23 — начальный снимок
Первая выгрузка контекста проекта для переноса в Claude Code.
Источник истины остаётся в Claude.ai (память проекта плюс Google Drive).
При существенных изменениях (вебинар, блокеры, статусы) пересобрать комплект тем же промптом в Claude.ai и заменить файлы.

## 2026-09-03 — установлен UI/UX Pro Max
В `.claude/skills/` развёрнут набор скиллов UI/UX Pro Max v2.15.0 (nextlevelbuilder/ui-ux-pro-max-skill, MIT):
`ui-ux-pro-max`, `design`, `design-system`, `ui-styling`, `brand`, `slides`, `banner-design`.
Установка: `npx ui-ux-pro-max-cli init --ai claude`. Обновление: та же команда с `--force`.
Скрипт поиска `python3 .claude/skills/ui-ux-pro-max/scripts/search.py "<запрос>" --design-system` требует только Python 3.
