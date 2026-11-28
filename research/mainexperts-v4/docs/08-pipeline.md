# MainExperts. Воспроизведение исследования v4.0

26 ноября 2026 года

## Что входит в поставку

Исходный код разделяет загрузку, нормализацию, дедупликацию, классификацию, построение связей и публикацию отчётов. Закрытый набор содержит Parquet-наблюдения, таблицу уникальных ключей, классификацию и справочники.

| Слой | Назначение |
| --- | --- |
| `observations` | Все непустые строки, исходный запрос и ячейки, номер строки и листа, метрики и нормализованные значения |
| `sources`, `source_sheets` | Файл, ссылка, дата выгрузки из имени, дата модификации Drive, признаки усечения и идентичности, заголовки листов |
| `query_observation_keys` | Связь исходных наблюдений с дедуплицированным ключом |
| `queries` | Одно представительное наблюдение на нормализованную фразу, рынок и поисковик, с дополнительной областью для неизвестной географии |
| `query_labels` | Язык, намерение, основной и дополнительные кластеры, задача, гипотеза услуги, уровень доказательности |
| `query_journey` | Объединённая матрица. Описания и CTA вычисляются с помощью связей |
| `tasks`, `cluster_catalog`, `services`, `products` | Задачи v2, смысловые атомы, гипотезы услуг и продуктов |
| `conversions`, `conversion_intents`, `cta_localizations`, `elements` | Интерфейсы, привязки намерений, переводы CTA и события |
| `cluster_instances`, `regional_subclusters` | Наблюдённые L4 и L5 с числом ключей |

Пустой перевод означает, что русская формулировка запроса не проверялась. Пустая страна назначения означает, что формулировка не позволяет установить её с достаточной уверенностью.

## С готовыми данными

Распакуйте все семь архивов Parquet в одну папку `release-unpacked`. Сверьте контрольные суммы с `parquet-manifest.json`. CSV читаются отдельно от базы. Для запросов ко всем таблицам восстановите DuckDB.

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r pipeline/requirements.txt
python pipeline/export_parquet.py restore \
  --db mainexperts-v4.duckdb --stage stage --output release-unpacked
python pipeline/report_data.py --db mainexperts-v4.duckdb --output tables
```

```sql
SELECT search_market, service_id, evidence_level, count(*) AS phrases
FROM query_journey
WHERE service_id IN ('P09','P23','P24','P25')
GROUP BY ALL
ORDER BY service_id, search_market, evidence_level;

SELECT source_id, sheet, row_no, query_raw, target_raw, raw_cells
FROM query_observation_keys
WHERE query_id = '<query_id>'
ORDER BY source_id, sheet, row_no;
```

## С собственным доступом к Google Drive

Закрытая конфигурация содержит идентификаторы папок. Установите переменную окружения `MAINEXPERTS_DRIVE_ACCESS_TOKEN` с токеном чтения. Загрузчик использует Drive API. При ограничениях `files.export` крупный Google Sheet можно сохранить в XLSX с именем `<file_id>.xlsx` в `inputs/raw` и повторить запуск.

```bash
python pipeline/drive_pull.py --folders pipeline/config/drive-folders.private.json --input inputs
python pipeline/ingest.py --input inputs --stage stage --workers 7
python pipeline/warehouse.py stage --stage stage --work run --db mainexperts-v4.duckdb --workers 7
python pipeline/warehouse.py classify --stage stage --work run --db mainexperts-v4.duckdb --workers 7
python pipeline/warehouse.py integrate --stage stage --work run --db mainexperts-v4.duckdb --workers 7
python pipeline/report_data.py --db mainexperts-v4.duckdb --output tables
python pipeline/export_parquet.py observations --db mainexperts-v4.duckdb --stage stage --output release
python pipeline/export_parquet.py pack --db mainexperts-v4.duckdb --stage stage --output release
```

При повторе неизменённого прогона доступно возобновление `ingest.py --reuse` и `warehouse.py classify --resume`. При изменении правил, данных или схемы используйте новый каталог работы. Размер пакета нормализации — 20 000 строк. Классификация распараллелена по отпечатку ключа. Рекомендуется не менее 12 ГБ свободного диска.

## Нормализация и покрытие

- Исходная фраза сохраняется дословно. Ключ использует Unicode NFKC, нижний регистр и нормализованные разделители. Склейка синонимов происходит в кластерах, ключи остаются раздельными.
- География берётся из явного поля отчёта. Прямой отчёт Ahrefs имеет приоритет над Top Location, которому присвоен отдельный тип метрики. Глобальная частотность из Top Location-выгрузок сохранена в исходных ячейках. Поисковые системы и повторные наблюдения не суммируются.
- В выгрузках Keys-формата точная и широкая частотности сохранены отдельно. География этих файлов неизвестна. Папка применяется только как область происхождения неизвестного рынка.
- SHA-256 выделяет точные дубликаты. Все строки сохранены, число независимых файлов для ключа считается по отпечаткам. При несовпадении номинальных доменов у одинаковых файлов относительный URL остаётся без присвоения домена.
- Некорректные численные ячейки остаются пустыми в типизированном слое. Исходное значение доступно в `raw_cells`. Даты, появившиеся вместо чисел в XLSX, не реконструируются.
- Доказательство D3 требует формулировки о сторонней услуге. Платежи вузам, государственным органам и экзаменационным центрам имеют отдельного получателя. Уверенность — вес эвристики, а не откалиброванная вероятность.

## Карта и отчёты

CJM воспроизводится из оригинальной версии `journey-v3.yaml`, сводок и генератора из `.claude/skills/cjm-map` на коммите `14816a72b5a30579cf46a47084e6b0739cb2a36a`. Параметры запуска и проверки описаны в документации карты. Для PDF нужен Pandoc, WeasyPrint и шрифты с кириллицей, арабским и китайским. Книги Excel строятся из CSV/TSV через `render_matrix.py`, `workbooks.mjs` и `build_gap_xlsx.mjs`. Нужен средовый пакет `@oai/artifact-tool`.
