// Реестр ингест-адаптеров графа. Каждый адаптер: источник → staged узлы/связи
// с уже проставленными method + provenance. Фаза 0 — пусто (каркас проверяется
// на пустом графе). Фаза 1 подключит: education (из витрин), esco, onet, isco,
// curation. Порядок важен: сначала опорные узлы (Occupation/Direction), потом связи.

import type { GraphEdge, GraphNode } from '../types.ts';

export interface Staged { nodes: GraphNode[]; edges: GraphEdge[]; sources: { source: string; localFile?: string; records?: number }[] }

export type Ingestor = (ctx: IngestContext) => Promise<Staged> | Staged;

export interface IngestContext {
  appDir: string;
  /** Каталог с сырыми дампами источников (вне git); задаётся переменной GRAPH_RAW. */
  rawDir: string;
  buildDir: string;
}

// Фаза 1 наполнит этот список. Пока пусто — сборка валидирует пустой граф.
export const INGESTORS: Ingestor[] = [];

export async function ingestAll(ctx: IngestContext): Promise<Staged> {
  const all: Staged = { nodes: [], edges: [], sources: [] };
  for (const ing of INGESTORS) {
    const s = await ing(ctx);
    all.nodes.push(...s.nodes);
    all.edges.push(...s.edges);
    all.sources.push(...s.sources);
  }
  return all;
}
