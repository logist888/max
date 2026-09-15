import { ReactFlowProvider } from '@xyflow/react';
import { AnimatePresence } from 'framer-motion';
import { useViewGraph } from '@/hooks/useViewGraph';
import { useAppState } from '@/app/store';
import { Graph } from './Graph';
import { Inspector } from '@/features/inspector/Inspector';
import { SearchPanel } from '@/features/search/SearchPanel';
import { FilterBar } from '@/features/filters/FilterBar';
import { Legend } from '@/features/legend/Legend';

/** Область карты: граф React Flow + все накладываемые панели. */
export function Canvas() {
  const view = useViewGraph();
  const { selectedId, searchOpen, legendOpen, expandedLayers } = useAppState();
  const overview = expandedLayers.size === 0 && !selectedId;

  return (
    <div className="canvas">
      <ReactFlowProvider>
        <Graph view={view} />
      </ReactFlowProvider>

      {overview && (
        <div className="hint-pill">
          Кликните слой, чтобы раскрыть детали — перед вами архитектура за 30 секунд
        </div>
      )}

      <FilterBar />
      {legendOpen && <Legend />}

      <AnimatePresence>{selectedId && <Inspector />}</AnimatePresence>
      {searchOpen && <SearchPanel />}
    </div>
  );
}
