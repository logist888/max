#!/usr/bin/env bash
# Установка зависимостей. Среда эфемерна — запускать в начале сессии.
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
python3 -m pip install --quiet --disable-pip-version-check -r "$DIR/requirements.txt"
F=/usr/share/fonts/truetype/dejavu
if [ ! -f "$F/DejaVuSans-Oblique.ttf" ]; then
  echo "[setup] нет DejaVuSans-Oblique.ttf — курсив в PDF деградирует до прямого начертания (не критично)"
fi
echo "[setup] зависимости готовы"

# Второй remote — Bitbucket (зеркало на случай блокировки GitHub). Идемпотентно.
REPO="$DIR/.."
BB_URL="https://bitbucket.org/agafonov_agency/max.git"
if ! git -C "$REPO" remote get-url bitbucket >/dev/null 2>&1; then
  git -C "$REPO" remote add bitbucket "$BB_URL"
fi
# Учётные данные берём только из переменных окружения облачной среды, на диск не пишем.
# BITBUCKET_TOKEN — repository access token (логин x-token-auth) или API-токен Atlassian
# (тогда BITBUCKET_USER = e-mail аккаунта Atlassian).
if [ -n "${BITBUCKET_TOKEN:-}" ]; then
  git -C "$REPO" config credential.https://bitbucket.org.helper \
    '!f() { echo "username=${BITBUCKET_USER:-x-token-auth}"; echo "password=$BITBUCKET_TOKEN"; }; f'
  echo "[setup] bitbucket: remote и учётные данные настроены"
else
  echo "[setup] bitbucket: remote добавлен, BITBUCKET_TOKEN не задан — пуш в Bitbucket недоступен"
fi
