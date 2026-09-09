#!/usr/bin/env bash
# Установка окружения транскрипции. Среда эфемерна — запускать в начале сессии.
set -euo pipefail

MODELS_DIR="${ASR_MODELS_DIR:-$HOME/.cache/mainexperts-asr/models}"
K2="https://github.com/k2-fsa/sherpa-onnx/releases/download"

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "[setup] ставлю ffmpeg"
  DEBIAN_FRONTEND=noninteractive apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq ffmpeg
fi

echo "[setup] ставлю python-пакеты"
PIP_FLAGS="--quiet --disable-pip-version-check"
python3 -m pip install $PIP_FLAGS --break-system-packages \
  -r "$(cd "$(dirname "$0")" && pwd)/requirements.txt" 2>/dev/null ||
python3 -m pip install $PIP_FLAGS \
  -r "$(cd "$(dirname "$0")" && pwd)/requirements.txt"

mkdir -p "$MODELS_DIR"
cd "$MODELS_DIR"

# Эмбеддинги голоса: CAM++ (VoxCeleb), 29 МБ
if [ ! -f wespeaker_en_voxceleb_CAM++.onnx ]; then
  echo "[setup] качаю модель эмбеддингов голоса"
  curl -sSL --retry 3 -O "$K2/speaker-recongition-models/wespeaker_en_voxceleb_CAM++.onnx"
fi

# Сегментация речи: pyannote segmentation-3.0 в ONNX, 6 МБ
if [ ! -f sherpa-onnx-pyannote-segmentation-3-0/model.onnx ]; then
  echo "[setup] качаю модель сегментации речи"
  curl -sSL --retry 3 -O "$K2/speaker-segmentation-models/sherpa-onnx-pyannote-segmentation-3-0.tar.bz2"
  tar xjf sherpa-onnx-pyannote-segmentation-3-0.tar.bz2
  rm -f sherpa-onnx-pyannote-segmentation-3-0.tar.bz2
fi

# Модель распознавания (~1.6 ГБ) скачается сама при первом запуске из HuggingFace.
echo "[setup] окружение транскрипции готово: $MODELS_DIR"
