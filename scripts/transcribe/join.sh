#!/usr/bin/env bash
# Склеить части одной встречи в одну запись и назвать реальную длительность.
#
#   scripts/transcribe/join.sh raw/Встреча-2026-09-29.webm raw/Встреча-2026-09-29-p*.webm
#
# Клиенты режут длинную встречу на куски по 30 минут; на стыках теряются
# секунды, а иногда и минуты — между кусками бывает реальный перерыв. Скрипт
# печатает разрывы, чтобы это попало в шапку выжимки: в склейке пауз нет, и
# таймкоды расходятся с реальным временем встречи.
#
# Осторожно с длительностью: в webm после concat заголовок врёт. Правду говорит
# последний пакет аудио, его и печатаем.
set -u

if [ $# -lt 3 ]; then
    echo "нужно: $0 <выход.webm> <часть1> <часть2> [часть3 ...]" >&2
    exit 1
fi

out=$1
shift
list=$(mktemp)
sum=0

for f in "$@"; do
    [ -s "$f" ] || { echo "нет файла: $f" >&2; exit 1; }
    printf "file '%s'\n" "$(readlink -f "$f")" >> "$list"
    d=$(ffprobe -v error -select_streams a -show_entries packet=pts_time -of csv=p=0 "$f" | tail -1)
    printf "  %-44s %6.0f c\n" "$(basename "$f")" "$d"
    sum=$(python3 -c "print($sum + $d)")
    # время начала записи берём из имени файла: «... 14_08_28.webm»
    t=$(basename "$f" | grep -oE '[0-9]{2}_[0-9]{2}_[0-9]{2}' | tail -1 | tr '_' ':')
    [ -n "$t" ] && echo "     начало по имени файла: $t"
done

ffmpeg -v error -f concat -safe 0 -i "$list" -c copy -y "$out"
rm -f "$list"

real=$(ffprobe -v error -select_streams a -show_entries packet=pts_time -of csv=p=0 "$out" | tail -1)
python3 - "$sum" "$real" "$out" <<'PY'
import sys
want, got, out = float(sys.argv[1]), float(sys.argv[2]), sys.argv[3]
def hms(s): return f"{int(s//3600)}:{int(s%3600//60):02d}:{int(s%60):02d}"
print(f"склеено: {out}")
print(f"сумма частей {hms(want)}, в склейке {hms(got)}")
if abs(want - got) > 2:
    print(f"! расхождение {abs(want-got):.0f} c — проверить длительность по WAV после конвертации")
PY

echo
echo "Разрывы между частями (по времени в именах файлов) отметить в шапке выжимки:"
echo "в склейке их нет, поэтому к концу таймкоды уходят вперёд относительно встречи."
