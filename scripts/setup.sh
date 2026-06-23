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
