/**
 * Build the gap register, source catalog and observed input-coverage workbook.
 * Copy this module to a working directory linked to the artifact-tool runtime.
 */
import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const [config, staged, output, previewDir] = process.argv.slice(2);
if (!(config && staged && output)) {
  throw new Error("Usage: build_gap_xlsx.mjs CONFIG_DIR STAGE_SOURCES_JSON OUTPUT_XLSX [PREVIEW_DIR]");
}

const swatches = {
  blue: "#1B426D", navy: "#183557", ink: "#263D57",
  light: "#EDF4FA", white: "#FFFFFF", note: "#5C7185",
};
const tabs = {
  map: "Карта пробелов",
  files: "Охват файлов",
  sources: "Источники",
};
const names = {
  AE: "ОАЭ", AU: "Австралия", CA: "Канада", CH: "Швейцария", CN: "Китай",
  DE: "Германия", ES: "Испания", FR: "Франция", HK: "Гонконг", IT: "Италия",
  RU: "Россия / Москва", SG: "Сингапур", UK: "Великобритания", US: "США",
};
const kinds = {
  free_alternative: "Бесплатная альтернатива", instrument: "Измерение поиска",
  method: "Методика", official_context: "Официальная справка",
  official_payment: "Внешний платёж", official_register: "Официальный реестр",
  official_route: "Официальный маршрут", own_metrics: "Собственные метрики",
  supplier: "Частное предложение", supplier_checkout_ui: "Корзина или покупка",
  supplier_lead: "Лид или запись", supplier_priced: "Публичный тариф",
};

async function loadTsv(base) {
  const file = await fs.readFile(path.join(config, base), "utf8");
  const [keys, ...body] = file.trimEnd().split("\n").map(line => line.split("\t"));
  return body.map(cells => {
    if (cells.length !== keys.length) {
      throw new Error(`Invalid column count in ${base}: ${cells[0]}`);
    }
    return Object.fromEntries(keys.map((key, i) => [key, cells[i]]));
  });
}

function excelDate(value) {
  return Date.parse(value + "T00:00:00Z") / 864e5 + 25569;
}

function placeTable(sheet, { title, note, headers, data, widths, key, minHeight = 25 }) {
  const toCol = (number) => String.fromCharCode(65 + number);
  const last = toCol(headers.length - 1);
  sheet.showGridLines = false;
  const titleBox = sheet.getRange("A2");
  titleBox.values = [[title]];
  titleBox.format.font = { name: "Golos Text", size: 16, color: swatches.navy, bold: true };
  titleBox.format.rowHeight = 26;
  sheet.getRange("A3").values = [[note]];
  sheet.getRange("A3").format.font = { name: "Golos Text", size: 9, color: swatches.note };
  sheet.getRange("A3").format.rowHeight = 18;
  const header = sheet.getRange(`A5:${last}5`);
  header.values = [headers];
  header.format.fill = swatches.blue;
  header.format.font = { name: "Golos Text", size: 10, bold: true, color: swatches.white };
  header.format.wrapText = true;
  header.format.verticalAlignment = "center";
  header.format.horizontalAlignment = "center";
  header.format.rowHeight = 32;
  const lastRow = 5 + data.length;
  const cells = sheet.getRange(`A6:${last}${lastRow}`);
  cells.values = data;
  cells.format.font = { name: "Golos Text", size: 10, color: swatches.ink };
  cells.format.verticalAlignment = "center";
  cells.format.wrapText = true;
  widths.forEach((width, i) => {
    const col = toCol(i);
    sheet.getRange(`${col}1:${col}${lastRow}`).format.columnWidth = width;
  });
  data.forEach((record, index) => {
    const row = sheet.getRange(`A${index + 6}:${last}${index + 6}`);
    if (index % 2 === 1) row.format.fill = swatches.light;
    const lines = Math.max(...record.map((value, i) =>
      (String(value).startsWith("http") ? 1 : Math.ceil(String(value).length / (widths[i] * 0.86)))));
    row.format.rowHeight = Math.max(minHeight, lines * 14 + 8);
  });
  if (data.length > 18) sheet.freezePanes.freezeRows(5);
  const table = sheet.tables.add(`A5:${last}${lastRow}`, true, key);
  table.style = "TableStyleLight9";
  table.showFilterButton = true;
  return lastRow;
}

const [gaps, refs, inventory] = await Promise.all([
  loadTsv("gap_register.tsv"), loadTsv("gap_sources.tsv"),
  fs.readFile(staged, "utf8").then(JSON.parse),
]);
const book = Workbook.create();
const mapSheet = book.worksheets.add(tabs.map);
const files = book.worksheets.add(tabs.files);
const sources = book.worksheets.add(tabs.sources);

const ordered = [...gaps].sort((a, b) =>
  Number(a.PRIORITY) - Number(b.PRIORITY) || a.GAP_ID.localeCompare(b.GAP_ID));
placeTable(mapSheet, {
  title: "MainExperts v4.0 · Приоритеты сбора",
  note: "1 — проверить перед продуктовым тестом. 2 — расширить покрытие и измерения.",
  headers: ["Код", "Приоритет", "Измерение", "Область", "Признак пробела",
    "Что измерить", "Действие", "Условие закрытия", "Ограничение"],
  data: ordered.map(r => [r.GAP_ID, Number(r.PRIORITY), r.DIMENSION, r.SCOPE,
    r.TRIGGER, r.MEASURE, r.ACTION, r.DONE_WHEN, r.LIMIT]),
  widths: [8, 12, 22, 24, 39, 39, 51, 43, 35], key: "GapRegister",
});
mapSheet.getRange(`B6:B${5 + gaps.length}`).format.horizontalAlignment = "center";

const sourceRows = refs.map(r => [
  r.SOURCE_ID, names[r.DESTINATION] ?? "Международный", r.LANGUAGE_HINT,
  kinds[r.SOURCE_TYPE], r.SOURCE_NAME, r.FOCUS, r.PAYER_BOUNDARY, r.USE, r.LIMIT,
  excelDate(r.ACCESSED), r.URL,
]);
placeTable(sources, {
  title: "MainExperts v4.0 · Каталог источников",
  note: "Источник описывает измерение, официальный порядок, альтернативу или предложение.",
  headers: ["Код", "Система", "Языки сбора", "Тип", "Источник", "Что покрывает",
    "Получатель платежа", "Как использовать", "Ограничение", "Проверено", "URL"],
  data: sourceRows, widths: [9, 19, 19, 27, 32, 32, 30, 42, 44, 15, 60],
  key: "GapSources",
});
sources.getRange(`J6:J${5 + sourceRows.length}`).setNumberFormat("dd.mm.yyyy");
sources.getRange(`K6:K${5 + sourceRows.length}`).format.wrapText = false;
sources.getRange(`K6:K${5 + sourceRows.length}`).format.font.color = "#235D95";

const aggregate = Object.fromEntries(Object.keys(names).map(k => [k, [0, 0, 0, 0, 0]]));
const numberByHash = new Map();
let references = 0;
const notes = {
  CA: "Повтор файла UnivCan по SHA-256.", DE: "Повтор файла DAAD по SHA-256.",
  RU: "Семь файлов отмечены лимитом. Повтор с конфликтующими номинальными доменами.",
  UK: "Три записи без запроса в BigFuture, Educatly и Studyportals.",
};
let skipped = 0;
for (const source of inventory) {
  if (source.status === "reference_inventory") references += 1;
  else if (["processed", "partial_schema"].includes(source.status)) {
    const count = aggregate[source.region];
    if (!count) throw new Error(`Unknown folder: ${source.region}`);
    count[0] += 1;
    count[1] += source.sheets.reduce((sum, row) => sum + row.rows, 0);
    count[2] += source.sheets.reduce((sum, row) => sum + row.query_rows, 0);
    count[3] += Number(Boolean(source.incomplete_filename));
    count[4] += source.bytes_local;
    if (source.sha256) numberByHash.set(source.sha256, (numberByHash.get(source.sha256) ?? 0) + 1);
  } else skipped += 1;
}
const coverageRows = Object.entries(aggregate).map(([id, row]) => [names[id], ...row, notes[id] ?? ""]);
const endRow = placeTable(files, {
  title: "MainExperts v4.0 · Охват исходных файлов",
  note: "Группировка по папкам. Частотность, рынок запроса и число уникальных фраз считаются отдельно.",
  headers: ["Папка", "Файлы", "Непустые строки", "Строки с запросом", "Признак лимита",
    "Прочитано байт", "Замечание"],
  data: coverageRows, widths: [21, 11, 18, 19, 16, 18, 54],
  key: "SourceCoverage", minHeight: 26,
});
files.getRange(`B6:F${endRow + 1}`).setNumberFormat("#,##0");
files.getRange(`A${endRow + 1}`).values = [["Итого"]];
files.getRange(`B${endRow + 1}:F${endRow + 1}`).formulas =
  [["B", "C", "D", "E", "F"].map(col => `=SUM(${col}6:${col}${endRow})`)];
files.getRange(`A${endRow + 1}:G${endRow + 1}`).format.fill = "#DCEAF6";
files.getRange(`A${endRow + 1}:G${endRow + 1}`).format.font =
  { name: "Golos Text", size: 10, color: swatches.navy, bold: true };
files.getRange(`A${endRow + 1}:G${endRow + 1}`).format.rowHeight = 26;
const duplicateGroups = [...numberByHash.values()].filter(count => count > 1).length;
files.getRange(`A${endRow + 3}:B${endRow + 5}`).values =
  [["Справочные PDF", references], ["Группы повторов SHA-256", duplicateGroups], ["Пропуск выгрузки", skipped]];
files.getRange(`A${endRow + 3}:A${endRow + 5}`).format.wrapText = true;
files.getRange(`A${endRow + 3}:B${endRow + 5}`).format.rowHeight = 26;
book.recalculate();
const actual = files.getRange(`B${endRow + 1}:F${endRow + 1}`).values[0];
const expected = Object.values(aggregate).reduce((total, row) =>
  total.map((sum, i) => sum + row[i]), [0, 0, 0, 0, 0]);
if (JSON.stringify(actual) !== JSON.stringify(expected)) {
  throw new Error(`Coverage totals differ: ${JSON.stringify({ actual, expected })}`);
}
const checked = await book.inspect({
  kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!",
  options: { useRegex: true, maxResults: 30 }, summary: "Formula error scan",
});
console.log(checked.ndjson);
if (previewDir) {
  await fs.mkdir(previewDir, { recursive: true });
  for (const [index, sheet, range] of [[1,tabs.map,"A1:F11"],[2,tabs.files,`A1:G${endRow + 5}`],[3,tabs.sources,"A1:G10"]]) {
    const image = await book.render({ sheetName: sheet, range, scale: 1, format: "png" });
    await fs.writeFile(path.join(previewDir, `gaps-${index}.png`), new Uint8Array(await image.arrayBuffer()));
  }
}
await fs.mkdir(path.dirname(output), { recursive: true });
const workbookFile = await SpreadsheetFile.exportXlsx(book);
await workbookFile.save(output);
