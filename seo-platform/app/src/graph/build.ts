// Оркестратор сборки графа. Идемпотентен: одинаковый вход даёт одинаковый выход
// (детерминированные id + реестр). Зеркалит pipeline/run.ts.
// Запуск: npm run graph   (сырые дампы — в каталоге GRAPH_RAW, вне git).
//
// acquire → ingest → (resolve/merge — фаза 1) → validate → emit + manifest + report.
// Любой жёсткий отказ гейта = exit(1), как в конвейере витрин.

import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { ingestAll } from './ingest/index.ts';
import { validate } from './validate.ts';
import type { GraphManifest } from './types.ts';

const HERE = dirname(fileURLToPath(import.meta.url));
const APP = resolve(HERE, '../..');
const BUILD = join(APP, 'build', 'graph');
const RAW = process.env.GRAPH_RAW || resolve(APP, '../data/graph/raw');
const RUN_ID = process.env.GRAPH_RUN_ID || 'g-local'; // без Date.now(): идемпотентность

const ctx = { appDir: APP, rawDir: RAW, buildDir: BUILD };

const staged = await ingestAll(ctx);
// Стабильный порядок — идемпотентность артефакта.
staged.nodes.sort((a, b) => a.id.localeCompare(b.id));
staged.edges.sort((a, b) => a.id.localeCompare(b.id));

console.log(`Ингест: узлов ${staged.nodes.length}, связей ${staged.edges.length}, источников ${staged.sources.length}`);

const report = validate(staged.nodes, staged.edges, APP);
for (const w of report.warnings.slice(0, 20)) console.warn(`  предупреждение: ${w}`);
if (!report.ok) {
  for (const e of report.errors) console.error(`  ошибка: ${e}`);
  console.error('Граф отклонён гейтами.');
  process.exit(1);
}

mkdirSync(BUILD, { recursive: true });
writeFileSync(join(BUILD, 'nodes.jsonl'), staged.nodes.map((n) => JSON.stringify(n)).join('\n') + (staged.nodes.length ? '\n' : ''));
writeFileSync(join(BUILD, 'edges.jsonl'), staged.edges.map((e) => JSON.stringify(e)).join('\n') + (staged.edges.length ? '\n' : ''));

const manifest: GraphManifest = {
  builtAt: process.env.GRAPH_BUILT_AT || 'unknown',
  runId: RUN_ID,
  sources: staged.sources,
  counts: {
    nodes: report.stats.nodes,
    edges: report.stats.edges,
    byNodeType: report.stats.byNodeType,
    byEdgeType: report.stats.byEdgeType,
  },
};
writeFileSync(join(BUILD, 'manifest.json'), JSON.stringify(manifest, null, 2));
writeFileSync(join(BUILD, 'report.json'), JSON.stringify(report.stats, null, 2));

console.log('Гейты: зелено. Отчёт:', JSON.stringify(report.stats, null, 2));
console.log(`Граф собран в ${BUILD}`);
