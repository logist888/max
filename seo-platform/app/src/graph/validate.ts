// Гейты качества графа (fail-closed, как pipeline/contract.ts).
// Дублируется независимым Python-контролёром graph_audit.py — расхождение
// их выводов само по себе повод для разбирательства.

import { readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import type { GraphEdge, GraphNode, Method, Status } from './types.ts';

const METHODS: Method[] = ['authoritative', 'crosswalk', 'inferred', 'curated'];
const STATUSES: Status[] = ['факт', 'гипотеза', 'требует-проверки'];
// Потолки доверия для выводимых/курируемых связей: они не могут быть «факт».
const INFERRED_CEIL = 0.8;

export interface ValidationReport {
  ok: boolean;
  errors: string[];
  warnings: string[];
  stats: {
    nodes: number;
    edges: number;
    byNodeType: Record<string, number>;
    byEdgeType: Record<string, number>;
    factWithoutProvenance: number;
    edgesExcludedFromPublic: number;
  };
}

interface Licenses { licenses: Record<string, { publicOutput: boolean; status: string }>; }

function loadLicenses(appDir: string): Licenses['licenses'] {
  const raw = JSON.parse(readFileSync(join(appDir, 'config/graph/licenses.json'), 'utf8')) as Licenses;
  return raw.licenses;
}

/** Публична ли связь как ФАКТ: только authoritative (или проверенный crosswalk),
 *  статус факт, все источники с publicOutput и не blocked. */
export function isPublicFact(
  el: GraphNode | GraphEdge,
  method: Method,
  licenses: Licenses['licenses'],
): boolean {
  if (el.status !== 'факт') return false;
  if (method === 'inferred' || method === 'curated') return false;
  if (el.provenance.length === 0) return false;
  return el.provenance.every((p) => {
    const lic = licenses[p.license];
    return lic && lic.publicOutput && lic.status !== 'blocked';
  });
}

export function validate(nodes: GraphNode[], edges: GraphEdge[], appDir: string): ValidationReport {
  const errors: string[] = [];
  const warnings: string[] = [];
  const licenses = loadLicenses(appDir);
  const byNodeType: Record<string, number> = {};
  const byEdgeType: Record<string, number> = {};

  // --- Узлы: конверт, уникальность id, полнота провенанса
  const ids = new Set<string>();
  let factWithoutProvenance = 0;
  for (const n of nodes) {
    byNodeType[n.type] = (byNodeType[n.type] ?? 0) + 1;
    const at = `node ${n.id}`;
    if (!/^me:[a-z]+:/.test(n.id)) errors.push(`${at}: id не в формате me:<type>:<key>`);
    if (ids.has(n.id)) errors.push(`${at}: дубль id`);
    ids.add(n.id);
    if (!STATUSES.includes(n.status)) errors.push(`${at}: неизвестный status «${n.status}»`);
    if (typeof n.confidence !== 'number' || n.confidence < 0 || n.confidence > 1) {
      errors.push(`${at}: confidence вне 0..1`);
    }
    // «Премиум-факт»: факт без источника недопустим → понизить (тут — ошибка сборки,
    // ингест обязан ставить требует-проверки, если источника нет).
    if (n.status === 'факт' && n.provenance.length === 0) {
      factWithoutProvenance += 1;
      errors.push(`${at}: status=факт без provenance (правило премиум-факта)`);
    }
    // labels.ru для публичных типов — предупреждение, не ошибка (может быть требует-проверки).
    if ((n.type === 'Occupation' || n.type === 'EducationDirection') && !n.labels.ru && n.status === 'факт') {
      warnings.push(`${at}: факт без русской метки (labels.ru)`);
    }
  }

  // --- Связи: конверт, висячие концы, согласованность method/confidence
  const edgeIds = new Set<string>();
  let excludedFromPublic = 0;
  for (const e of edges) {
    byEdgeType[e.type] = (byEdgeType[e.type] ?? 0) + 1;
    const at = `edge ${e.id}`;
    if (edgeIds.has(e.id)) errors.push(`${at}: дубль id`);
    edgeIds.add(e.id);
    if (!ids.has(e.from)) errors.push(`${at}: висячий конец from=${e.from}`);
    if (!ids.has(e.to)) errors.push(`${at}: висячий конец to=${e.to}`);
    if (!METHODS.includes(e.method)) errors.push(`${at}: неизвестный method «${e.method}»`);
    if (typeof e.confidence !== 'number' || e.confidence < 0 || e.confidence > 1) {
      errors.push(`${at}: confidence вне 0..1`);
    }
    // Метод ↔ статус ↔ доверие: выводимое/курируемое не может быть фактом
    // и не может превышать потолок доверия.
    if ((e.method === 'inferred' || e.method === 'curated')) {
      if (e.status === 'факт') errors.push(`${at}: ${e.method}-связь со status=факт (запрещено)`);
      if (e.confidence > INFERRED_CEIL) {
        errors.push(`${at}: ${e.method}-связь с confidence>${INFERRED_CEIL}`);
      }
    }
    if (e.method === 'authoritative' && e.provenance.length === 0) {
      errors.push(`${at}: authoritative без provenance`);
    }
    // Каждый источник связи должен иметь запись в реестре лицензий.
    for (const p of e.provenance) {
      if (!licenses[p.license]) errors.push(`${at}: источник ссылается на неизвестную лицензию «${p.license}»`);
    }
    if (!isPublicFact(e, e.method, licenses)) excludedFromPublic += 1;
  }

  const cap = 40;
  if (errors.length > cap) { errors.splice(cap); errors.push('…и другие ошибки (обрезано)'); }

  return {
    ok: errors.length === 0,
    errors,
    warnings,
    stats: {
      nodes: nodes.length,
      edges: edges.length,
      byNodeType,
      byEdgeType,
      factWithoutProvenance,
      edgesExcludedFromPublic: excludedFromPublic,
    },
  };
}
