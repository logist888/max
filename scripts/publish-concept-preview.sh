#!/usr/bin/env bash
# Обновляет превью концепта портала и карты CJM в отдельной ветке claude/concept-preview.
# Источник правды — docs/html/ рабочей ветки; в превью-ветке лежит копия в seo-platform/app/public/concept/
# (Cloudflare Pages собирает seo-platform/app). Ветка не сливается в main.
# Запуск из корня репозитория: scripts/publish-concept-preview.sh
set -euo pipefail
BR=claude/concept-preview
SRC=docs/html
ROOT=$(git rev-parse --show-toplevel)
cd "$ROOT"
git fetch -q origin "$BR"
W=$(mktemp -d)
trap 'git worktree remove --force "$W" 2>/dev/null || true' EXIT
git worktree add -q -B "$BR" "$W" "origin/$BR"
D="$W/seo-platform/app/public/concept"
mkdir -p "$D/img"
cp "$SRC/portal-concept-standalone.html" "$D/portal-concept-standalone.html"
cp "$SRC/cjm-poisk-vse-napravleniya.html" "$D/cjm-poisk-vse-napravleniya.html"
cp "$SRC"/img/* "$D/img/"
# обычная версия с папкой img и запретом индексации
python3 - "$SRC/portal-concept.html" "$D/portal-concept.html" <<'PY'
import sys
s = open(sys.argv[1], encoding="utf-8").read()
rob = '<meta name="robots" content="noindex,nofollow">'
if rob not in s:
    s = s.replace("<head>", "<head>\n" + rob, 1)
open(sys.argv[2], "w", encoding="utf-8").write(s)
PY
cd "$W"
git add -A
if git diff --cached --quiet; then echo "Превью уже актуально"; exit 0; fi
git commit -q -m "Обновление превью концепта и карты CJM

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_014ckeXSLRQghY76MRUBZb2u"
git push -q origin "$BR"
echo "Превью обновлено: ветка $BR"
