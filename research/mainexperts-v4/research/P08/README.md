# MainExperts CJM v4 · P08

Исследование проверки статуса образовательной организации, программы, площадки и права присуждать степень. Исходные коды Q08, J03, E25, E03, C-P08-F/O/A; R10 применяется к спорным случаям. Открытая регуляторная запись и коммерческое предложение подтверждаются отдельно. Подробные поисковые наблюдения, маршруты и скриншоты хранятся в пользовательском пакете.

```bash
python study.py /path/to/mainexperts-v4.duckdb /path/to/p08/data
python landings.py /path/to/p08
python review.py /path/to/p08/data/queries_pending.csv /path/to/p08/review_labels.csv --register-keys /path/to/p08/data/register-keys.txt
python landings.py /path/to/p08 --queue
python interactive/build.py /path/to/p08-evidence /path/to/mainexperts-p08-interactive.html
```

Связь с реестром устанавливается по всем исходным наблюдениям. Запись сопоставляется по предмету, схеме и периоду действия. Запросы поиска компании отделены от лицензирования поставщика, проверки отдельного диплома и миграционного допуска. HTML включает фильтры диапазона, вида, наличия оценки и D1–D3. Ноль и пустое значение различаются.
