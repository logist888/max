import { useMemo } from 'react';
import type { Inspectable, ResolvedRelation } from '@/types';
import type { Decision, Rule } from '@/types';
import { ENTITY_BY_ID } from '@/data';
import { DOMAIN_GRAPH, NODE_INDEX } from '@/app/graph';
import { useAppState } from '@/app/store';
import { getRelatedDecisions, getRelatedRules, getRelations } from '@/utils/relations';

export interface SelectionDetail {
  readonly entity: Inspectable;
  readonly incoming: readonly ResolvedRelation[];
  readonly outgoing: readonly ResolvedRelation[];
  readonly rules: readonly Rule[];
  readonly decisions: readonly Decision[];
}

/** Выбранная сущность со всеми разрешёнными связями — вход для инспектора. */
export function useSelectionDetail(): SelectionDetail | null {
  const { selectedId } = useAppState();
  return useMemo<SelectionDetail | null>(() => {
    if (!selectedId) return null;
    const entity = ENTITY_BY_ID.get(selectedId);
    if (!entity) return null;
    const { incoming, outgoing } = getRelations(DOMAIN_GRAPH, selectedId, NODE_INDEX);
    return {
      entity,
      incoming,
      outgoing,
      rules: getRelatedRules(selectedId),
      decisions: getRelatedDecisions(entity),
    };
  }, [selectedId]);
}
