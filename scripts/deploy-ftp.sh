#!/usr/bin/env bash
# Деплой vuz-navigator.ru на FTP без всякого CI — с любого компьютера.
#
# Нужны только: node 22+, npm, lftp, curl.
#   Ubuntu/Debian:  sudo apt install lftp
#   macOS:          brew install lftp
#
# Учётные данные берутся из переменных окружения или из файла .env.deploy
# рядом со скриптом (он в .gitignore, в репозиторий не попадёт):
#   FTP_SERVER=31.31.197.39
#   FTP_USERNAME=u3591005
#   FTP_PASSWORD=пароль
#   FTP_REMOTE_DIR=/www/vuz-navigator.ru
#   SITE_URL=https://vuz-navigator.ru      # необязательно
#   FTP_DELETE_STALE=true                  # необязательно, удалять лишнее на сервере
#
# Запуск:
#   ./scripts/deploy-ftp.sh --discover   показать структуру FTP, ничего не менять
#   ./scripts/deploy-ftp.sh --dry-run    собрать и показать, что было бы залито
#   ./scripts/deploy-ftp.sh --deploy     собрать и залить
#   ./scripts/deploy-ftp.sh --deploy --force-full   залить всё заново

set -euo pipefail

MODE=""
FORCE_FULL="false"
for arg in "$@"; do
  case "$arg" in
    --discover)   MODE="discover" ;;
    --dry-run)    MODE="dry-run" ;;
    --deploy)     MODE="deploy" ;;
    --force-full) FORCE_FULL="true" ;;
    -h|--help)    sed -n '2,28p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Неизвестный аргумент: $arg. Смотрите --help"; exit 2 ;;
  esac
done
[ -n "$MODE" ] || { echo "Укажите режим: --discover | --dry-run | --deploy"; exit 2; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
APP_DIR="$REPO_ROOT/seo-platform/app"

# shellcheck disable=SC1091
[ -f "$SCRIPT_DIR/.env.deploy" ] && { set -a; . "$SCRIPT_DIR/.env.deploy"; set +a; }

SITE_URL="${SITE_URL:-https://vuz-navigator.ru}"
FTP_DELETE_STALE="${FTP_DELETE_STALE:-false}"

say() { printf '\n\033[1m== %s\033[0m\n' "$1"; }
die() { printf '\n\033[31mОШИБКА: %s\033[0m\n' "$1" >&2; exit 1; }

say "Проверка окружения"
for cmd in lftp curl; do
  command -v "$cmd" >/dev/null 2>&1 || die "не установлен $cmd"
done
: "${FTP_SERVER:?не задан FTP_SERVER}"
: "${FTP_USERNAME:?не задан FTP_USERNAME}"
: "${FTP_PASSWORD:?не задан FTP_PASSWORD}"
[ "$MODE" = "discover" ] || : "${FTP_REMOTE_DIR:?не задан FTP_REMOTE_DIR (узнайте режимом --discover)}"
echo "  режим: $MODE | сервер: $FTP_SERVER | сайт: $SITE_URL"

export LFTP_PASSWORD="$FTP_PASSWORD"
LFTP_COMMON='set ftp:passive-mode on
set ftp:ssl-allow true
set ssl:verify-certificate no
set net:timeout 20
set net:max-retries 3
set net:reconnect-interval-base 5
set mirror:parallel-transfer-count 5
set xfer:log no'

if [ "$MODE" = "discover" ]; then
  say "Структура FTP (ничего не меняется)"
  lftp -u "$FTP_USERNAME" --env-password "$FTP_SERVER" <<LFTP
$LFTP_COMMON
set cmd:fail-exit no
echo "=== корень ==="
ls
echo "=== типовые каталоги сайта ==="
ls www
ls public_html
ls data
ls www/vuz-navigator.ru
ls data/www/vuz-navigator.ru
bye
LFTP
  echo
  echo "Найденный корень сайта пропишите в FTP_REMOTE_DIR."
  exit 0
fi

command -v node >/dev/null 2>&1 || die "не установлен node"
node_major="$(node -p 'process.versions.node.split(".")[0]')"
[ "$node_major" -ge 22 ] || die "нужен node 22+, установлен $(node -v)"

cd "$APP_DIR"

say "Установка зависимостей"
npm ci

say "Сборка витрин данных"
npm run pipeline && npm run graph

say "Сборка сайта ($SITE_URL)"
SITE_URL="$SITE_URL" npm run build

say "Проверки до заливки"
pages="$(find dist -name '*.html' | wc -l | tr -d ' ')"
[ "$pages" -ge 9000 ] || die "собрано только $pages страниц (ожидалось >9000). Заливка отменена."
for f in dist/index.html dist/404.html dist/sitemap-index.xml; do
  [ -s "$f" ] || die "нет или пуст $f. Заливка отменена."
done
grep -q "canonical\" href=\"$SITE_URL" dist/index.html \
  || die "canonical не указывает на $SITE_URL. Проверьте SITE_URL."
echo "  страниц: $pages | размер: $(du -sh dist | cut -f1) — проверки пройдены"

FLAGS="--reverse --continue --parallel=5 --verbose=1"
# Сверка по размеру: у свежего клона все файлы «новые», сверка по времени
# бесполезна. Правку без изменения размера пропустит — на этот случай --force-full.
[ "$FORCE_FULL" = "true" ] || FLAGS="$FLAGS --ignore-time"
[ "$FTP_DELETE_STALE" = "true" ] && FLAGS="$FLAGS --delete"
[ "$MODE" = "dry-run" ] && FLAGS="$FLAGS --dry-run"

say "Синхронизация на $FTP_REMOTE_DIR"
echo "  флаги: $FLAGS"
lftp -u "$FTP_USERNAME" --env-password "$FTP_SERVER" <<LFTP
$LFTP_COMMON
mirror $FLAGS dist/ "$FTP_REMOTE_DIR"
bye
LFTP

if [ "$MODE" = "deploy" ]; then
  say "Проверка прода"
  fail=0
  for p in / /vuzy/ /gorod/moskva/ /professiya/ /specialnosti/ /sitemap-index.xml; do
    code="$(curl -s -o /dev/null -w '%{http_code}' -m 25 "$SITE_URL$p" || echo 000)"
    printf '  %s  %s\n' "$code" "$p"
    [ "$code" = "200" ] || fail=1
  done
  [ "$fail" = 0 ] || die "часть страниц не отвечает 200."
  echo
  echo "Готово: сайт залит и отвечает."
else
  echo
  echo "Пробный прогон завершён. Для реальной заливки: --deploy"
fi
