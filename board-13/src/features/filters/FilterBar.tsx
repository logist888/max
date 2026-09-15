import { motion } from 'framer-motion';
import type { FilterFacet } from '@/app/store';
import { useActions, useAppState } from '@/app/store';
import { TRAFFIC_SOURCES } from '@/data';
import {
  LANGUAGE_LABEL,
  MARKET_LABEL,
  OWNER_LABEL,
  STATUS_LABEL,
  TEMPERATURE_LABEL,
} from '@/data/labels';
import { isFiltersActive } from '@/utils/filters';
import { Chip } from '@/components/ui/Chip';
import { IconButton } from '@/components/ui/IconButton';

interface FacetDef {
  readonly facet: FilterFacet;
  readonly label: string;
  readonly options: readonly { readonly v: string; readonly l: string }[];
}

const FACETS: readonly FacetDef[] = [
  {
    facet: 'markets',
    label: 'Рынок',
    options: [
      { v: 'CIS', l: MARKET_LABEL.CIS },
      { v: 'MENA', l: MARKET_LABEL.MENA },
      { v: 'BOTH', l: MARKET_LABEL.BOTH },
    ],
  },
  {
    facet: 'temperatures',
    label: 'Температура',
    options: (['cold', 'warm', 'hot', 'nurture'] as const).map((v) => ({ v, l: TEMPERATURE_LABEL[v] })),
  },
  {
    facet: 'statuses',
    label: 'Статус ячейки',
    options: (['active', 'scaling', 'paused', 'stopped', 'draft'] as const).map((v) => ({ v, l: STATUS_LABEL[v] })),
  },
  {
    facet: 'landingKinds',
    label: 'Тип посадочной',
    options: [
      { v: 'funnel', l: 'воронковая' },
      { v: 'transactional', l: 'транзакционная' },
    ],
  },
  {
    facet: 'languages',
    label: 'Язык',
    options: (['RU', 'EN', 'AR'] as const).map((v) => ({ v, l: LANGUAGE_LABEL[v] })),
  },
  {
    facet: 'owners',
    label: 'Владелец',
    options: (['marketing_lead', 'content_lead', 'partner_lead', 'crm_lead'] as const).map((v) => ({
      v,
      l: OWNER_LABEL[v],
    })),
  },
  {
    facet: 'channels',
    label: 'Источник',
    options: TRAFFIC_SOURCES.map((s) => ({ v: s.id, l: s.name })),
  },
];

export function FilterBar() {
  const { filters, filtersOpen } = useAppState();
  const actions = useActions();
  if (!filtersOpen) return null;
  const active = isFiltersActive(filters);

  return (
    <motion.div
      className="panel filterbar"
      initial={{ y: 12, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.16 }}
      style={{ maxHeight: 'calc(100vh - 140px)', overflowY: 'auto' }}
    >
      <div className="filterbar__inner">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
          <strong style={{ fontSize: 12.5 }}>Фильтры</strong>
          <div style={{ display: 'flex', gap: 6 }}>
            {active && (
              <button className="btn btn--ghost" onClick={actions.clearFilters}>
                Сбросить
              </button>
            )}
            <IconButton icon="x" title="Закрыть фильтры" ghost onClick={() => actions.setFiltersOpen(false)} />
          </div>
        </div>
        {FACETS.map((f) => {
          const set = filters[f.facet] as ReadonlySet<string>;
          return (
            <div className="filter-group" key={f.facet}>
              <div className="filter-group__label">{f.label}</div>
              <div className="filter-group__chips">
                {f.options.map((o) => (
                  <Chip
                    key={o.v}
                    label={o.l}
                    interactive
                    on={set.has(o.v)}
                    onClick={() => actions.toggleFilter(f.facet, o.v)}
                  />
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </motion.div>
  );
}
