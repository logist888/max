#!/usr/bin/env bash
# Весь конвейер по одной записи: разметка по картинке, потом распознавание.
#
#   scripts/transcribe/run.sh raw/Встреча-2026-09-29.webm \
#       --participants "Игорь А.,Александр Бондаренко,Вадим Х." -s 4 -e titanet
#
# Всё после имени файла уходит в diarize_asr.py, кроме --participants и --band —
# они предназначены разметке по картинке. Разметка считается первой: она быстрая
# и по её итогу видно, можно ли вообще опираться на подсветку.
#
# Запускать в фоне: на трёх часах записи распознавание идёт около часа.
#   nohup scripts/transcribe/run.sh raw/файл.webm -s 4 > /tmp/tr.log 2>&1 &
set -u

[ $# -ge 1 ] || { echo "нужно: $0 <запись> [ключи]" >&2; exit 1; }
src=$1; shift
[ -s "$src" ] || { echo "нет файла: $src" >&2; exit 1; }

here=$(dirname "$0")
stem=$(basename "$src"); stem=${stem%.*}
work=transcripts/.work
mkdir -p "$work" transcripts

participants=""
band=1080
asr_args=()
while [ $# -gt 0 ]; do
    case $1 in
        --participants) participants=$2; shift 2 ;;
        --band) band=$2; shift 2 ;;
        *) asr_args+=("$1"); shift ;;
    esac
done

has_video=$(ffprobe -v error -select_streams v -show_entries stream=codec_type -of csv=p=0 "$src" | head -1)
tags="$work/$stem.tags.json"

if [ -n "$has_video" ]; then
    if [ -s "$tags" ]; then
        echo "разметка по картинке уже есть: $tags"
    else
        echo "=== разметка по картинке ==="
        set -- python3 "$here/video_speaker_tags.py" "$src" -o "$tags" --band "$band"
        [ -n "$participants" ] && set -- "$@" --participants "$participants"
        "$@"
    fi
    asr_args+=(--video-tags "$tags")
else
    echo "видеопотока нет — роли только по голосу, имена назначать вручную"
fi

echo
echo "=== распознавание ==="
python3 "$here/diarize_asr.py" "$src" -o transcripts/ "${asr_args[@]}"

echo
echo "Дальше: прочитать transcripts/$stem.md целиком и собрать выжимку"
echo "по шаблону .claude/skills/transcribe/assets/summary.html → transcripts/$stem.summary.html"
echo "Выдача — тройка: .md, .txt, .summary.html"
