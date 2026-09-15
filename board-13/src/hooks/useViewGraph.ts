import { useMemo } from 'react';
import type { ViewGraph } from '@/types/graph';
import { DOMAIN_GRAPH } from '@/app/graph';
import { useAppState } from '@/app/store';
import { composeView } from '@/utils/viewGraph';
import { isFiltersActive, nodeMatchesFilters } from '@/utils/filters';

/** Композиция представления (узлы/рёбра с раскладкой) из текущего состояния. */
export function useViewGraph(): ViewGraph {
  const { expandedLayers, filters } = useAppState();
  return useMemo<ViewGraph>(() => {
    const filtersActive = isFiltersActive(filters);
    return composeView(DOMAIN_GRAPH, {
      expandedLayers,
      filtersActive,
      matches: (node) => nodeMatchesFilters(node, filters),
    });
  }, [expandedLayers, filters]);
}
