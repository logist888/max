#!/usr/bin/env bash
# Скачать записи с Google Drive по идентификаторам файлов.
#
# Через MCP качать нельзя: download_file_content отдаёт base64 в контекст и на
# записи в сотни мегабайт непригоден. Здесь прямая загрузка с подтверждением,
# которое Drive требует для файлов больше 100 МБ.
#
#   scripts/transcribe/fetch.sh raw/Встреча-2026-09-29 ID1 ID2 ID3
#
# При нескольких идентификаторах имена получают суффикс -p1, -p2 и так далее —
# в том порядке, в каком они перечислены. Порядок задаёт склейку, поэтому
# перечислять части нужно по времени начала записи, а не так, как их вернул Drive.
set -u

if [ $# -lt 2 ]; then
    echo "нужно: $0 <путь-без-расширения> <file_id> [file_id ...]" >&2
    exit 1
fi

base=$1
shift
mkdir -p "$(dirname "$base")"
total=$#
i=0

for id in "$@"; do
    i=$((i + 1))
    if [ "$total" -eq 1 ]; then stem="$base"; else stem="$base-p$i"; fi
    done_already=$(ls "$stem".* 2>/dev/null | head -1)
    if [ -n "$done_already" ]; then
        echo "уже скачано: $done_already ($(stat -c%s "$done_already") Б)"
        continue
    fi
    out="$stem.part"

    jar=$(mktemp)
    page=$(mktemp)
    curl -sSL -c "$jar" "https://drive.google.com/uc?export=download&id=$id" -o "$page"

    if head -c 200 "$page" | grep -qi '<!DOCTYPE\|<html'; then
        # страница подтверждения: забираем uuid из формы
        uuid=$(grep -oE 'name="uuid" value="[^"]+"' "$page" | head -1 | sed 's/.*value="//;s/"//')
        curl -sSL -b "$jar" \
            "https://drive.usercontent.google.com/download?id=$id&export=download&confirm=t&uuid=$uuid" \
            -o "$out"
    else
        mv "$page" "$out"
    fi
    rm -f "$jar" "$page"

    size=$(stat -c%s "$out" 2>/dev/null || echo 0)
    if [ "$size" -lt 100000 ]; then
        echo "ОШИБКА: $out весит $size Б — Drive вернул не файл, а страницу" >&2
        head -c 200 "$out" >&2; echo >&2
        exit 1
    fi

    # расширение — по тому, что реально пришло: Drive отдаёт и webm, и m4a, и mp4
    fmt=$(ffprobe -v error -show_entries format=format_name -of csv=p=0 "$out" 2>/dev/null)
    case "$fmt" in
        *matroska*|*webm*) ext=webm ;;
        *mp4*|*m4a*|*mov*) ext=$(ffprobe -v error -select_streams v -show_entries stream=codec_type \
                                 -of csv=p=0 "$out" 2>/dev/null | head -1 | grep -q video && echo mp4 || echo m4a) ;;
        *mp3*)             ext=mp3 ;;
        *wav*)             ext=wav ;;
        "")  echo "ОШИБКА: $out не читается как медиафайл" >&2; exit 1 ;;
        *)   ext=${fmt%%,*} ;;
    esac
    mv "$out" "$stem.$ext"
    echo "скачано: $stem.$ext $size"
done

echo "ГОТОВО: $i из $total"
echo "Сверить размеры с метаданными Drive перед склейкой."
