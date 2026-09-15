import { useMemo } from 'react';
import type { LayerId } from '@/types';
import { ALL_ENTITIES, LAYERS } from '@/data';
import { LAYER_COLORS } from '@/data/colors';
import { useActions, useAppState } from '@/app/store';
import { Icon } from '@/components/ui/Icon';

/**
 * Левый рельс слоёв. Полностью data-driven: перечень и порядок берутся из словаря LAYERS,
 * количество объектов — из ALL_ENTITIES. Клик по строке сворачивает/раскрывает слой.
 */
export function LayerRail() {
  const { expandedLayers } = useAppState();
  const actions = useActions();

  const counts = useMemo(() => {
    const map = new Map<LayerId, number>();
    for (const e of ALL_ENTITIES) map.set(e.layer, (map.get(e.layer) ?? 0) + 1);
    return map;
  }, []);

  return (
    <aside className="rail">
      <div className="rail__title">Слои архитектуры</div>
      {LAYERS.map((layer) => {
        const expanded = expandedLayers.has(layer.id);
        return (
          <div className="layer-row" key={layer.id} onClick={() => actions.toggleLayer(layer.id)}>
            <span className="layer-row__bar" style={{ background: LAYER_COLORS[layer.id].accent }} />
            <div style={{ minWidth: 0 }}>
              <div className="layer-row__name" style={{ color: LAYER_COLORS[layer.id].accent }}>
                {layer.title}
              </div>
              <div className="layer-row__sub">{layer.subtitle}</div>
            </div>
            <span className="layer-row__count">
              {counts.get(layer.id) ?? 0}
              <Icon name={expanded ? 'chevronDown' : 'chevronRight'} size={14} color="#94a3b8" />
            </span>
          </div>
        );
      })}
    </aside>
  );
}
