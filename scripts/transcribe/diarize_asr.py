#!/usr/bin/env python3
"""Транскрипция аудио/видео по говорящим с таймкодами.

Пайплайн (полностью локальный, CPU, без внешних API и ключей):
  1. ffmpeg          — любой контейнер → WAV 16 кГц моно
  2. sherpa-onnx     — диаризация: pyannote segmentation-3.0 (ONNX) + CAM++ эмбеддинги
                       + быстрая кластеризация → кто и когда говорит
  3. faster-whisper  — распознавание речи с таймкодами на уровне слов
  4. сшивка          — каждое слово получает говорящего по максимальному перекрытию,
                       слова собираются в реплики
  5. экспорт         — Markdown, SRT, JSON, TXT

Запуск: python3 scripts/transcribe/diarize_asr.py запись.webm -o transcripts/
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import wave
from dataclasses import dataclass, field, asdict
from pathlib import Path

MODELS_DIR = Path(os.environ.get("ASR_MODELS_DIR", Path.home() / ".cache/mainexperts-asr/models"))
SEGMENTATION_MODEL = MODELS_DIR / "sherpa-onnx-pyannote-segmentation-3-0" / "model.onnx"
EMBEDDINGS = {                      # модели голосовых эмбеддингов: имя → файл
    "campp": "wespeaker_en_voxceleb_CAM++.onnx",
    "titanet": "nemo_en_titanet_large.onnx",
}
EMBEDDING_MODEL = MODELS_DIR / EMBEDDINGS["campp"]
DEFAULT_ASR_MODEL = "deepdml/faster-whisper-large-v3-turbo-ct2"


# ── вспомогательное ────────────────────────────────────────────────────────────

def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def hms(sec: float, ms: bool = False) -> str:
    sec = max(0.0, float(sec))
    h, rem = divmod(int(sec), 3600)
    m, s = divmod(rem, 60)
    if ms:
        return f"{h:02d}:{m:02d}:{s:02d},{int((sec - int(sec)) * 1000):03d}"
    return f"{h:02d}:{m:02d}:{s:02d}"


@dataclass
class Word:
    start: float
    end: float
    text: str
    speaker: int = -1


@dataclass
class Turn:
    speaker: int
    start: float
    end: float
    text: str
    words: list = field(default_factory=list, repr=False)


# ── шаг 1: аудио ───────────────────────────────────────────────────────────────

def to_wav16k(src: Path, workdir: Path) -> Path:
    """Приводит любой вход к WAV 16 кГц моно 16 бит. Уже подходящий файл не трогает."""
    if src.suffix.lower() == ".wav":
        try:
            with wave.open(str(src), "rb") as w:
                if w.getframerate() == 16000 and w.getnchannels() == 1 and w.getsampwidth() == 2:
                    return src
        except wave.Error:
            pass
    if shutil.which("ffmpeg") is None:
        sys.exit("ffmpeg не найден. Установите: apt-get install -y ffmpeg")
    dst = workdir / (src.stem + ".16k.wav")
    if dst.exists() and dst.stat().st_size > 0:
        log(f"аудио уже извлечено: {dst.name}")
        return dst
    log(f"извлекаю аудио: {src.name} → {dst.name}")
    subprocess.run(
        ["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(src),
         "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(dst)],
        check=True,
    )
    return dst


def read_wav(path: Path):
    import numpy as np
    with wave.open(str(path), "rb") as w:
        assert w.getframerate() == 16000 and w.getnchannels() == 1 and w.getsampwidth() == 2
        raw = w.readframes(w.getnframes())
    samples = np.frombuffer(raw, dtype="<i2").astype("float32") / 32768.0
    return samples, len(samples) / 16000.0


# ── шаг 2: диаризация ──────────────────────────────────────────────────────────

def diarize(wav: Path, num_speakers: int, threshold: float, threads: int, cache: Path | None,
            embedding: Path = EMBEDDING_MODEL):
    """Возвращает список (start, end, speaker_id). Результат кешируется в JSON."""
    if cache and cache.exists():
        log(f"диаризация из кеша: {cache.name}")
        return [tuple(x) for x in json.loads(cache.read_text())]

    import sherpa_onnx

    for p in (SEGMENTATION_MODEL, embedding):
        if not p.exists():
            sys.exit(f"нет модели: {p}\nЗапустите scripts/transcribe/setup.sh")

    cfg = sherpa_onnx.OfflineSpeakerDiarizationConfig(
        segmentation=sherpa_onnx.OfflineSpeakerSegmentationModelConfig(
            pyannote=sherpa_onnx.OfflineSpeakerSegmentationPyannoteModelConfig(
                model=str(SEGMENTATION_MODEL)),
            num_threads=threads,
        ),
        embedding=sherpa_onnx.SpeakerEmbeddingExtractorConfig(
            model=str(embedding), num_threads=threads),
        clustering=sherpa_onnx.FastClusteringConfig(
            num_clusters=num_speakers if num_speakers > 0 else -1,
            threshold=threshold),
        min_duration_on=0.3,
        min_duration_off=0.5,
    )
    if not cfg.validate():
        sys.exit("некорректная конфигурация диаризации")

    sd = sherpa_onnx.OfflineSpeakerDiarization(cfg)
    samples, dur = read_wav(wav)
    mode = f"speakers={num_speakers}" if num_speakers > 0 else f"auto, threshold={threshold}"
    log(f"диаризация: {dur / 60:.1f} мин, {mode}")

    state = {"pct": -10}

    def progress(processed: int, total: int) -> int:
        pct = int(100 * processed / max(total, 1))
        if pct >= state["pct"] + 10:
            state["pct"] = pct - pct % 10
            log(f"  диаризация {pct}%")
        return 0

    t0 = time.time()
    result = sd.process(samples, callback=progress).sort_by_start_time()
    segs = [(round(s.start, 3), round(s.end, 3), s.speaker) for s in result]
    log(f"диаризация готова: {len(segs)} сегментов, "
        f"{len({s[2] for s in segs})} голосов, {time.time() - t0:.0f} с")
    if cache:
        cache.write_text(json.dumps(segs, ensure_ascii=False))
    return segs


# ── шаг 3: распознавание ───────────────────────────────────────────────────────

def transcribe(wav: Path, model_name: str, language: str, threads: int,
               beam: int, cache: Path | None):
    """Возвращает список Word. Результат кешируется в JSON."""
    if cache and cache.exists():
        log(f"распознавание из кеша: {cache.name}")
        return [Word(**w) for w in json.loads(cache.read_text())]

    from faster_whisper import WhisperModel

    log(f"загружаю модель ASR: {model_name}")
    model = WhisperModel(model_name, device="cpu", compute_type="int8", cpu_threads=threads)
    _, dur = read_wav(wav)
    log(f"распознавание: {dur / 60:.1f} мин аудио, язык={language or 'auto'}, beam={beam}")

    segments, info = model.transcribe(
        str(wav),
        language=language or None,
        beam_size=beam,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500),
        word_timestamps=True,
        condition_on_previous_text=False,   # не тянуть галлюцинации по цепочке
    )
    words: list[Word] = []
    t0 = time.time()
    next_report = 300.0
    for seg in segments:
        for w in (seg.words or []):
            txt = w.word.strip()
            if txt:
                words.append(Word(round(w.start, 3), round(w.end, 3), txt))
        if seg.end >= next_report:
            el = time.time() - t0
            log(f"  распознано {hms(seg.end)} из {hms(dur)} "
                f"(прошло {el / 60:.1f} мин, осталось ~{(dur - seg.end) * el / max(seg.end, 1) / 60:.0f} мин)")
            next_report = seg.end + 300.0
    log(f"распознавание готово: {len(words)} слов, {time.time() - t0:.0f} с")
    if cache:
        cache.write_text(json.dumps([asdict(w) for w in words], ensure_ascii=False))
    return words


# ── шаг 4: сшивка ──────────────────────────────────────────────────────────────

def assign_speakers(words, segs) -> None:
    """Каждому слову — говорящий с максимальным перекрытием; пустым — ближайший сегмент."""
    if not segs:
        return
    starts = [s[0] for s in segs]
    import bisect
    for w in words:
        i = max(0, bisect.bisect_left(starts, w.start) - 2)
        best, best_ov = -1, 0.0
        nearest, nearest_gap = -1, float("inf")
        for st, en, spk in segs[i:i + 8]:
            if st > w.end + 30:
                break
            ov = min(w.end, en) - max(w.start, st)
            if ov > best_ov:
                best_ov, best = ov, spk
            gap = max(st - w.end, w.start - en, 0.0)
            if gap < nearest_gap:
                nearest_gap, nearest = gap, spk
        w.speaker = best if best > -1 else nearest


def name_clusters_by_video(words, tags_path: Path):
    """Имена кластерам по видео, разметка слов — по голосу.

    Когда диаризация уже разделила голоса чисто, вести разметку по подсветке
    вредно: она переключается с задержкой и дробит реплики. Тогда от видео нужно
    только одно — как зовут каждый голос.
    """
    import bisect
    from collections import defaultdict

    data = json.loads(tags_path.read_text(encoding="utf-8"))
    single = [s for s in data["spans"] if not s.get("disputed")]
    if not single:
        log("видеоразметка без однозначных интервалов — имена не подставлены")
        return None
    starts = [s["start"] for s in single]

    hit: dict[int, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    spoken: dict[int, float] = defaultdict(float)
    for w in words:
        spoken[w.speaker] += max(w.end - w.start, 0.01)
        i = max(0, bisect.bisect_left(starts, w.start) - 1)
        for s in single[i:i + 4]:
            if s["start"] > w.end:
                break
            ov = min(w.end, s["end"]) - max(w.start, s["start"])
            if ov > 0:
                hit[w.speaker][s["name"]] += ov

    names, report = {}, []
    for spk in sorted(spoken):
        h = hit.get(spk)
        if not h:
            continue
        best = max(h, key=h.get)
        rival = max((v for k, v in h.items() if k != best), default=0.0)
        if h[best] > 2 * max(rival, 0.01):          # имя должно выигрывать уверенно
            names[str(spk)] = best
            report.append(f"{best} ← голос {spk} ({h[best]/60:.1f} против {rival/60:.1f} мин)")
    if not names:
        log("видео не дало уверенного соответствия голосам")
        return None
    log("имена голосам по видео: " + "; ".join(report))
    return names


def apply_video_names(words, tags_path: Path, min_share: float = 0.5,
                      ignore_voice: bool = False):
    """Расставляет имена участников по видеоразметке, диаризацией закрывая пробелы.

    Подсветка говорящего — сигнал более надёжный, чем кластеризация голосов: она
    привязана к участнику, а не к тембру, и не разваливается на десятки кластеров.
    Поэтому слово, попавшее в интервал с одним активным участником, получает имя
    напрямую. Там, где активны несколько или подсветки нет, слово берёт имя своего
    кластера — то, что чаще всего доставалось словам этого кластера напрямую.
    Кластер, у которого прямых назначений меньше min_share, остаётся под номером:
    приписать его наугад хуже, чем оставить номер.
    """
    import bisect
    from collections import defaultdict

    data = json.loads(tags_path.read_text(encoding="utf-8"))
    single = [s for s in data["spans"] if not s.get("disputed")]
    multi = [s for s in data["spans"] if s.get("disputed")]
    if not single:
        log("видеоразметка без однозначных интервалов — имена не подставлены")
        return None

    def overlaps(spans, starts, w):
        i = max(0, bisect.bisect_left(starts, w.start) - 1)
        out = {}
        for s in spans[i:i + 4]:
            if s["start"] > w.end:
                break
            ov = min(w.end, s["end"]) - max(w.start, s["start"])
            if ov > 0:
                out[s["name"]] = out.get(s["name"], 0.0) + ov
        return out

    s_starts = [s["start"] for s in single]
    m_starts = [s["start"] for s in multi]

    direct: dict[int, str] = {}
    by_cluster: dict[int, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    spoken: dict[int, float] = defaultdict(float)
    for idx, w in enumerate(words):
        spoken[w.speaker] += max(w.end - w.start, 0.01)
        ov = overlaps(single, s_starts, w)
        if ov:
            name = max(ov, key=ov.get)
            direct[idx] = name
            by_cluster[w.speaker][name] += ov[name]

    # имя кластера — то, что чаще всего доставалось его словам напрямую.
    # Кластер, где чужой речи почти столько же, сколько своей, ничего не решает:
    # такой голос разделён плохо, и опираться на него нельзя
    cluster_name: dict[int, str] = {}
    for spk, hits in (by_cluster.items() if not ignore_voice else []):
        if sum(hits.values()) < min_share * spoken[spk]:
            continue
        ranked = sorted(hits.values(), reverse=True)
        rival = ranked[1] if len(ranked) > 1 else 0.0
        if ranked[0] > 1.5 * max(rival, 0.01):
            cluster_name[spk] = max(hits, key=hits.get)
    if not cluster_name:
        log("голоса разделены слишком грязно — промежутки размечаются по соседней подсветке")

    named = list(dict.fromkeys(
        [n for _, n in sorted(direct.items())] + list(cluster_name.values())))
    order = {name: i for i, name in enumerate(named)}
    for spk in sorted(spoken):
        order.setdefault(f"__cluster_{spk}", len(order))

    from_video = from_cluster = from_near = 0
    for idx, w in enumerate(words):
        if idx in direct:
            key, from_video = direct[idx], from_video + 1
        else:
            # в спорном интервале выбираем среди активных того, кто ближе кластеру
            active = set(overlaps(multi, m_starts, w))
            hits = ({} if ignore_voice or w.speaker not in cluster_name
                    else by_cluster.get(w.speaker, {}))
            candidates = {n: v for n, v in hits.items() if n in active} or hits
            if candidates:
                key, from_cluster = max(candidates, key=candidates.get), from_cluster + 1
            elif w.speaker in cluster_name:
                key = cluster_name[w.speaker]
                from_cluster += 1
            else:
                # голосу верить нельзя — берём подсветку, ближайшую по времени:
                # в диалоге слово в паузе почти всегда принадлежит соседней реплике
                j = min(max(bisect.bisect_left(s_starts, w.start) - 1, 0), len(single) - 1)
                near = min(single[max(j - 1, 0):j + 2],
                           key=lambda s: max(s["start"] - w.end, w.start - s["end"], 0.0))
                gap = max(near["start"] - w.end, w.start - near["end"], 0.0)
                if gap <= 3.0:
                    key, from_near = near["name"], from_near + 1
                else:
                    key = f"__cluster_{w.speaker}"
        order.setdefault(key, len(order))
        w.speaker = order[key]

    names = {str(i): n for n, i in order.items() if not n.startswith("__cluster_")}
    stats = {"по видео": from_video, "по голосу": from_cluster,
             "по соседней подсветке": from_near,
             "без имени": len(words) - from_video - from_cluster - from_near}
    log(f"имена: {len(names)} участников; {from_video} слов по видео, {from_cluster} — по "
        f"голосу, {from_near} — по соседней подсветке, {stats['без имени']} — без имени")
    return names, stats


def split_reliability(words) -> str:
    """Насколько можно верить разметке по ролям.

    Смена говорящего посреди потока речи, без паузы, почти всегда ошибка
    разделения: люди перехватывают слово в паузе, а не поверх слога. Доля таких
    смен — простая и честная оценка того, режет ли диаризация по репликам или по
    случайным местам.
    """
    # короткие поддакивания («да», «угу», «понял») звучат поверх чужой речи —
    # это свойство живого диалога, а не ошибка; считаем только смены, после
    # которых человек действительно взял слово
    runs = []
    for w in words:
        if runs and runs[-1][0] == w.speaker:
            runs[-1][1].append(w)
        else:
            runs.append((w.speaker, [w]))
    tight = total = 0
    for prev_run, run in zip(runs, runs[1:]):
        if len(run[1]) < 5:
            continue
        total += 1
        if run[1][0].start - prev_run[1][-1].end < 0.3:
            tight += 1
    if total < 10:
        return "оценить нельзя: смен говорящего слишком мало"
    share = tight * 100 // total
    verdict = ("разделение надёжное" if share < 25 else
               "разделение спорное, роли проверять" if share < 50 else
               "разделение ненадёжно, ролям не верить")
    return f"{verdict} ({share}% смен без паузы)"


def build_turns(words, max_gap: float = 1.5) -> list[Turn]:
    """Слова → реплики: новый блок при смене говорящего или паузе длиннее max_gap."""
    turns: list[Turn] = []
    for w in words:
        if turns and turns[-1].speaker == w.speaker and w.start - turns[-1].end <= max_gap:
            t = turns[-1]
            t.end = w.end
            t.words.append(w)
        else:
            turns.append(Turn(w.speaker, w.start, w.end, "", [w]))
    for t in turns:
        text = " ".join(w.text for w in t.words)
        text = re.sub(r"\s+([,.!?;:…])", r"\1", text)
        text = re.sub(r"\s{2,}", " ", text).strip()
        t.text = text
    return [t for t in turns if t.text]


# ── шаг 5: экспорт ─────────────────────────────────────────────────────────────

def speaker_name(spk: int, names: dict) -> str:
    return names.get(str(spk), names.get(f"speaker_{spk}", f"Говорящий {spk + 1}"))


def write_md(turns, path: Path, names: dict, meta: dict) -> None:
    lines = [f"# Транскрипт: {meta['source']}", ""]
    lines += [
        f"- Длительность: {hms(meta['duration'])}",
        f"- Голосов распознано: {meta['speakers']}",
        f"- Модель распознавания: {meta['asr_model']}",
        f"- Разделение по голосам: {meta['diarization']}",
        f"- Имена участников: {meta['names_source']}",
        *([f"- Достоверность разделения: {meta['split_reliability']}"]
          if meta.get("split_reliability") else []),
        f"- Собрано: {meta['created']}",
        "",
    ]
    st = meta.get("word_attribution")
    if st:
        total = sum(st.values()) or 1
        lines += [
            "Откуда взята принадлежность слова говорящему: "
            + ", ".join(f"{k} — {v * 100 // total}%" for k, v in st.items() if v),
            "",
        ]
    lines += [
        "Разметка автоматическая. Перекрывающаяся речь приписывается одному участнику, "
        "короткие вставки липнут к соседней реплике, термины и суммы распознаются с "
        "ошибками. Цифры и цитаты для внешних материалов сверяются с записью.",
        "",
        "---",
        "",
    ]
    for t in turns:
        lines.append(f"**[{hms(t.start)} – {hms(t.end)}] {speaker_name(t.speaker, names)}**")
        lines.append("")
        lines.append(t.text)
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_txt(turns, path: Path, names: dict, meta: dict) -> None:
    """То же содержание, что в Markdown, но без разметки — для чтения и вставки куда угодно."""
    lines = [f"ТРАНСКРИПТ: {meta['source']}", ""]
    lines += [
        f"Длительность: {hms(meta['duration'])}",
        f"Голосов распознано: {meta['speakers']}",
        f"Модель распознавания: {meta['asr_model']}",
        f"Разделение по голосам: {meta['diarization']}",
        f"Имена участников: {meta['names_source']}",
        *([f"Достоверность разделения: {meta['split_reliability']}"]
          if meta.get("split_reliability") else []),
        f"Собрано: {meta['created']}",
        "",
    ]
    st = meta.get("word_attribution")
    if st:
        total = sum(st.values()) or 1
        lines += ["Откуда взята принадлежность слова говорящему: "
                  + ", ".join(f"{k} — {v * 100 // total}%" for k, v in st.items() if v), ""]
    lines += [
        "Разметка автоматическая. Перекрывающаяся речь приписывается одному участнику,",
        "короткие вставки липнут к соседней реплике, термины и суммы распознаются с",
        "ошибками. Цифры и цитаты для внешних материалов сверяются с записью.",
        "",
        "-" * 70,
        "",
    ]
    for t in turns:
        lines.append(f"[{hms(t.start)} – {hms(t.end)}] {speaker_name(t.speaker, names)}")
        lines.append(t.text)
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_srt(turns, path: Path, names: dict) -> None:
    out, i = [], 1
    for t in turns:
        # длинные реплики режем по ~180 символов, чтобы субтитр читался
        chunks, cur = [], ""
        for w in t.words:
            cur = f"{cur} {w.text}".strip()
            if len(cur) >= 180:
                chunks.append((cur, w.end))
                cur = ""
        if cur:
            chunks.append((cur, t.end))
        start = t.start
        for text, end in chunks:
            out.append(f"{i}\n{hms(start, ms=True)} --> {hms(end, ms=True)}\n"
                       f"{speaker_name(t.speaker, names)}: {text}\n")
            i += 1
            start = end
    path.write_text("\n".join(out), encoding="utf-8")


def write_json(turns, path: Path, names: dict, meta: dict) -> None:
    data = {
        "meta": meta,
        "speakers": {str(s): speaker_name(s, names)
                     for s in sorted({t.speaker for t in turns})},
        "turns": [
            {"speaker": t.speaker, "name": speaker_name(t.speaker, names),
             "start": round(t.start, 2), "end": round(t.end, 2),
             "start_hms": hms(t.start), "text": t.text}
            for t in turns
        ],
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ── CLI ────────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(
        description="Транскрипция по говорящим с таймкодами (локально, CPU)")
    ap.add_argument("input", type=Path, help="аудио или видео (webm, mp4, mp3, wav, m4a…)")
    ap.add_argument("-o", "--outdir", type=Path, default=Path("transcripts"),
                    help="каталог результатов (по умолчанию transcripts/)")
    ap.add_argument("-s", "--speakers", type=int, default=0,
                    help="число говорящих; 0 — определить автоматически")
    ap.add_argument("--threshold", type=float, default=0.5,
                    help="порог кластеризации при авторежиме: ниже — больше голосов")
    ap.add_argument("-l", "--language", default="ru", help="язык речи ('' — автоопределение)")
    ap.add_argument("-m", "--model", default=DEFAULT_ASR_MODEL, help="модель faster-whisper")
    ap.add_argument("-t", "--threads", type=int, default=os.cpu_count() or 4)
    ap.add_argument("-e", "--embedding", default="campp", choices=sorted(EMBEDDINGS),
                    help="модель голосовых эмбеддингов: campp быстрее, "
                         "titanet точнее на похожих голосах")
    ap.add_argument("--beam", type=int, default=1, help="beam size: 1 быстро, 5 точнее и дольше")
    ap.add_argument("--names", type=Path, help='JSON вида {"0": "Максим", "1": "Игорь"}')
    ap.add_argument("--video-tags", type=Path,
                    help="JSON от video_speaker_tags.py: имена участников по подсветке в записи")
    ap.add_argument("--video-only", action="store_true",
                    help="размечать только по подсветке, голосовые кластеры игнорировать: "
                         "для записей, где диаризация не разделила участников")
    ap.add_argument("--video-names-only", action="store_true",
                    help="брать из видео только имена голосов, разметку вести по голосу: "
                         "так реплики не дробятся, когда диаризация и так разделила чисто")
    ap.add_argument("--formats", default="md,txt,srt,json")
    ap.add_argument("--no-diarize", action="store_true", help="без разделения по голосам")
    ap.add_argument("--workdir", type=Path, help="каталог для WAV и кеша (по умолчанию рядом с выходом)")
    args = ap.parse_args()

    if not args.input.exists():
        sys.exit(f"нет файла: {args.input}")

    args.outdir.mkdir(parents=True, exist_ok=True)
    workdir = args.workdir or (args.outdir / ".work")
    workdir.mkdir(parents=True, exist_ok=True)
    stem = args.input.stem

    names = json.loads(args.names.read_text(encoding="utf-8")) if args.names else {}

    t_all = time.time()
    wav = to_wav16k(args.input, workdir)
    _, duration = read_wav(wav)

    segs = [] if args.no_diarize else diarize(
        wav, args.speakers, args.threshold, args.threads, workdir / f"{stem}.diar.json",
        MODELS_DIR / EMBEDDINGS[args.embedding])
    words = transcribe(wav, args.model, args.language, args.threads, args.beam,
                       workdir / f"{stem}.words.json")
    if not words:
        sys.exit("речь не распознана — проверьте аудиодорожку")

    assign_speakers(words, segs)
    word_stats = None
    if args.video_tags and args.video_names_only:
        video_names = name_clusters_by_video(words, args.video_tags)
        if video_names:
            names = {**video_names, **names}   # ручная карта имеет приоритет
    elif args.video_tags:
        result = apply_video_names(words, args.video_tags, ignore_voice=args.video_only)
        if result:
            video_names, word_stats = result
            names = {**video_names, **names}
    turns = build_turns(words)

    meta = {
        "source": args.input.name,
        "duration": round(duration, 1),
        "speakers": len({t.speaker for t in turns}),
        "asr_model": args.model,
        "diarization": (f"pyannote-segmentation-3.0 + {args.embedding} (sherpa-onnx)"
                        if segs else "нет"),
        "split_reliability": split_reliability(words) if segs else None,
        "names_source": ("подсветка говорящего в записи"
                         + (" (только имена голосов)" if args.video_names_only else "")
                         + (" (голос не учитывался)" if args.video_only else "")
                         if args.video_tags else "вручную"),
        "word_attribution": word_stats,
        "created": time.strftime("%Y-%m-%d %H:%M"),
        "turns": len(turns),
        "words": len(words),
    }

    formats = {f.strip() for f in args.formats.split(",") if f.strip()}
    written = []
    if "md" in formats:
        write_md(turns, args.outdir / f"{stem}.md", names, meta); written.append("md")
    if "txt" in formats:
        write_txt(turns, args.outdir / f"{stem}.txt", names, meta); written.append("txt")
    if "srt" in formats:
        write_srt(turns, args.outdir / f"{stem}.srt", names); written.append("srt")
    if "json" in formats:
        write_json(turns, args.outdir / f"{stem}.json", names, meta); written.append("json")

    log(f"готово за {(time.time() - t_all) / 60:.1f} мин: {args.outdir}/{stem}.{{{','.join(written)}}}")
    log(f"реплик: {meta['turns']}, голосов: {meta['speakers']}, слов: {meta['words']}")
    if meta.get("split_reliability"):
        log(f"достоверность разделения: {meta['split_reliability']}")


if __name__ == "__main__":
    main()
