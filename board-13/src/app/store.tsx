/**
 * Хранилище состояния приложения (context + reducer).
 * UI-компоненты не держат бизнес-состояния — только читают это хранилище и шлют действия.
 */

import {
  createContext,
  useContext,
  useMemo,
  useReducer,
  type Dispatch,
  type ReactNode,
} from 'react';
import type { ID, LayerId } from '@/types';
import { ENTITY_BY_ID, LAYERS } from '@/data';
import { DEFAULT_EXPANDED_LAYERS } from '@/constants/config';
import {
  EMPTY_FILTERS,
  type FilterState,
} from '@/utils/filters';

export interface FocusRequest {
  readonly id: ID;
  readonly nonce: number;
}

export interface AppState {
  readonly selectedId: ID | null;
  readonly hoveredId: ID | null;
  readonly expandedLayers: ReadonlySet<LayerId>;
  readonly filters: FilterState;
  readonly searchQuery: string;
  readonly searchOpen: boolean;
  readonly legendOpen: boolean;
  readonly filtersOpen: boolean;
  readonly showSecondary: boolean;
  readonly showForbidden: boolean;
  readonly focus: FocusRequest | null;
}

const ALL_LAYER_IDS = LAYERS.map((l) => l.id);

const initialState: AppState = {
  selectedId: null,
  hoveredId: null,
  expandedLayers: new Set(DEFAULT_EXPANDED_LAYERS),
  filters: EMPTY_FILTERS,
  searchQuery: '',
  searchOpen: false,
  legendOpen: false,
  filtersOpen: false,
  showSecondary: true,
  showForbidden: true,
  focus: null,
};

export type FilterFacet = keyof FilterState;

export type Action =
  | { type: 'SELECT'; id: ID | null }
  | { type: 'HOVER'; id: ID | null }
  | { type: 'FOCUS'; id: ID }
  | { type: 'TOGGLE_LAYER'; id: LayerId }
  | { type: 'EXPAND_ALL' }
  | { type: 'COLLAPSE_ALL' }
  | { type: 'TOGGLE_FILTER'; facet: FilterFacet; value: string }
  | { type: 'CLEAR_FILTERS' }
  | { type: 'SET_SEARCH'; query: string }
  | { type: 'SET_SEARCH_OPEN'; open: boolean }
  | { type: 'SET_LEGEND_OPEN'; open: boolean }
  | { type: 'SET_FILTERS_OPEN'; open: boolean }
  | { type: 'TOGGLE_SECONDARY' }
  | { type: 'TOGGLE_FORBIDDEN' }
  | { type: 'CLEAR_FOCUS' };

function toggleInSet<T extends string>(set: ReadonlySet<T>, value: T): Set<T> {
  const next = new Set(set);
  if (next.has(value)) next.delete(value);
  else next.add(value);
  return next;
}

function toggleFacet(f: FilterState, facet: FilterFacet, value: string): FilterState {
  switch (facet) {
    case 'markets':
      return { ...f, markets: toggleInSet(f.markets, value as never) };
    case 'languages':
      return { ...f, languages: toggleInSet(f.languages, value as never) };
    case 'channels':
      return { ...f, channels: toggleInSet(f.channels, value as never) };
    case 'temperatures':
      return { ...f, temperatures: toggleInSet(f.temperatures, value as never) };
    case 'landingKinds':
      return { ...f, landingKinds: toggleInSet(f.landingKinds, value as never) };
    case 'statuses':
      return { ...f, statuses: toggleInSet(f.statuses, value as never) };
    case 'owners':
      return { ...f, owners: toggleInSet(f.owners, value as never) };
    default:
      return f;
  }
}

/** Слой(и), которые нужно раскрыть, чтобы показать сущность на канве. */
function layersToReveal(id: ID): { layers: LayerId[]; focusId: ID } {
  const entity = ENTITY_BY_ID.get(id);
  if (!entity) return { layers: [], focusId: id };
  if (entity.kind === 'rule') {
    // Правило — не узел: раскрываем трафик и посадочные, фокус на основную посадочную.
    return { layers: ['traffic', 'landings'], focusId: entity.primaryLandingId };
  }
  return { layers: [entity.layer], focusId: id };
}

function reducer(state: AppState, action: Action): AppState {
  switch (action.type) {
    case 'SELECT':
      return { ...state, selectedId: action.id };
    case 'HOVER':
      return { ...state, hoveredId: action.id };
    case 'FOCUS': {
      const { layers, focusId } = layersToReveal(action.id);
      const expanded = new Set(state.expandedLayers);
      layers.forEach((l) => expanded.add(l));
      return {
        ...state,
        selectedId: action.id,
        expandedLayers: expanded,
        searchOpen: false,
        focus: { id: focusId, nonce: (state.focus?.nonce ?? 0) + 1 },
      };
    }
    case 'TOGGLE_LAYER': {
      const expanded = new Set(state.expandedLayers);
      if (expanded.has(action.id)) expanded.delete(action.id);
      else expanded.add(action.id);
      return { ...state, expandedLayers: expanded };
    }
    case 'EXPAND_ALL':
      return { ...state, expandedLayers: new Set(ALL_LAYER_IDS) };
    case 'COLLAPSE_ALL':
      return { ...state, expandedLayers: new Set() };
    case 'TOGGLE_FILTER':
      return { ...state, filters: toggleFacet(state.filters, action.facet, action.value) };
    case 'CLEAR_FILTERS':
      return { ...state, filters: EMPTY_FILTERS };
    case 'SET_SEARCH':
      return { ...state, searchQuery: action.query };
    case 'SET_SEARCH_OPEN':
      return { ...state, searchOpen: action.open };
    case 'SET_LEGEND_OPEN':
      return { ...state, legendOpen: action.open };
    case 'SET_FILTERS_OPEN':
      return { ...state, filtersOpen: action.open };
    case 'TOGGLE_SECONDARY':
      return { ...state, showSecondary: !state.showSecondary };
    case 'TOGGLE_FORBIDDEN':
      return { ...state, showForbidden: !state.showForbidden };
    case 'CLEAR_FOCUS':
      return { ...state, focus: null };
    default:
      return state;
  }
}

const StateContext = createContext<AppState | null>(null);
const DispatchContext = createContext<Dispatch<Action> | null>(null);

export function AppStateProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reducer, initialState);
  return (
    <StateContext.Provider value={state}>
      <DispatchContext.Provider value={dispatch}>{children}</DispatchContext.Provider>
    </StateContext.Provider>
  );
}

export function useAppState(): AppState {
  const ctx = useContext(StateContext);
  if (!ctx) throw new Error('useAppState must be used within AppStateProvider');
  return ctx;
}

export function useDispatch(): Dispatch<Action> {
  const ctx = useContext(DispatchContext);
  if (!ctx) throw new Error('useDispatch must be used within AppStateProvider');
  return ctx;
}

/** Связанные экшены — удобные обёртки над dispatch. */
export function useActions() {
  const dispatch = useDispatch();
  return useMemo(
    () => ({
      select: (id: ID | null) => dispatch({ type: 'SELECT', id }),
      hover: (id: ID | null) => dispatch({ type: 'HOVER', id }),
      focus: (id: ID) => dispatch({ type: 'FOCUS', id }),
      toggleLayer: (id: LayerId) => dispatch({ type: 'TOGGLE_LAYER', id }),
      expandAll: () => dispatch({ type: 'EXPAND_ALL' }),
      collapseAll: () => dispatch({ type: 'COLLAPSE_ALL' }),
      toggleFilter: (facet: FilterFacet, value: string) =>
        dispatch({ type: 'TOGGLE_FILTER', facet, value }),
      clearFilters: () => dispatch({ type: 'CLEAR_FILTERS' }),
      setSearch: (query: string) => dispatch({ type: 'SET_SEARCH', query }),
      setSearchOpen: (open: boolean) => dispatch({ type: 'SET_SEARCH_OPEN', open }),
      setLegendOpen: (open: boolean) => dispatch({ type: 'SET_LEGEND_OPEN', open }),
      setFiltersOpen: (open: boolean) => dispatch({ type: 'SET_FILTERS_OPEN', open }),
      toggleSecondary: () => dispatch({ type: 'TOGGLE_SECONDARY' }),
      toggleForbidden: () => dispatch({ type: 'TOGGLE_FORBIDDEN' }),
      clearFocus: () => dispatch({ type: 'CLEAR_FOCUS' }),
    }),
    [dispatch],
  );
}
