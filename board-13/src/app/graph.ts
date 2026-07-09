/**
 * Синглтоны производного графа. Доменный граф чист и неизменен — строим один раз.
 */

import type { ID } from '@/types';
import { buildDomainGraph } from '@/utils/graphBuilder';
import { buildNodeIndex } from '@/utils/relations';

export const DOMAIN_GRAPH = buildDomainGraph();
export const NODE_INDEX = buildNodeIndex(DOMAIN_GRAPH);

/** Соседи каждого узла (для подсветки связанных при выборе). */
export const NEIGHBORS: ReadonlyMap<ID, ReadonlySet<ID>> = (() => {
  const map = new Map<ID, Set<ID>>();
  const link = (a: ID, b: ID) => {
    const set = map.get(a) ?? new Set<ID>();
    set.add(b);
    map.set(a, set);
  };
  for (const e of DOMAIN_GRAPH.edges) {
    link(e.source, e.target);
    link(e.target, e.source);
  }
  return map;
})();
