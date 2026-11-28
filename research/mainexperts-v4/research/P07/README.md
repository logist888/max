# MainExperts v4.0 · P07. Аналитическое сравнение вариантов

Границы: Q07 и Q06.04, состояние J03, бесплатная таблица E07, проверенный разбор R03. Рейтинг, отзывы, показатели выпускников и их сопоставимость размечаются отдельно. Публичное предложение с ценой не повышает поисковую доказательность до D3.

```bash
python study.py /path/to/mainexperts-v4.duckdb /path/to/study/data
python landings.py /path/to/study
python review.py /path/to/study/data/queries_pending.csv /path/to/study/review_labels.csv --ranking-keys /path/to/study/data/ranking-keys.txt
python landings.py /path/to/study --queue
python interactive/build.py /path/to/p07-evidence /path/to/mainexperts-p07-interactive.html
```

Расширяющий проход сверяет рейтинговый URL по всем связанным наблюдениям. Числовая оценка хранится отдельно от вида метрики и уровня D1–D3. Дубли выгрузок не служат независимым подтверждением. Исходные запросы, наблюдения и снимки находятся в закрытом комплекте.
