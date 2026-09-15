import { useActions, useAppState } from '@/app/store';
import { APP_META } from '@/constants/config';
import { Icon } from '@/components/ui/Icon';
import { IconButton } from '@/components/ui/IconButton';
import { isFiltersActive } from '@/utils/filters';

/** Верхняя панель управления: бренд, поиск, раскрытие слоёв, тумблеры связей, фильтры, легенда. */
export function Toolbar() {
  const { showSecondary, showForbidden, legendOpen, filtersOpen, filters } = useAppState();
  const actions = useActions();

  return (
    <header className="toolbar">
      <div className="toolbar__brand">
        <span className="toolbar__badge">БОРД {APP_META.boardNo}</span>
        <span className="toolbar__title">System Map</span>
        <span className="toolbar__subtitle">{APP_META.subtitle}</span>
      </div>

      <div className="toolbar__spacer" />

      <button className="btn" onClick={() => actions.setSearchOpen(true)} title="Поиск (⌘K)">
        <Icon name="search" size={15} />
        Поиск
        <span className="search__kbd" style={{ marginLeft: 4 }}>⌘K</span>
      </button>

      <div className="toolbar__group">
        <button className="btn" onClick={actions.expandAll} title="Развернуть все слои">
          <Icon name="maximize" size={14} /> Развернуть
        </button>
        <button className="btn" onClick={actions.collapseAll} title="Свернуть до архитектуры">
          <Icon name="layers" size={14} /> Свернуть
        </button>
      </div>

      <div className="toolbar__group">
        <button
          className={`btn${showSecondary ? ' btn--active' : ''}`}
          onClick={actions.toggleSecondary}
          title="Показать дополнительные связи (допустимые посадочные, отдача данных)"
        >
          Доп. связи
        </button>
        <button
          className={`btn${showForbidden ? ' btn--active' : ''}`}
          onClick={actions.toggleForbidden}
          title="Показать запрещённые связи (красный пунктир)"
        >
          Запреты
        </button>
      </div>

      <div className="toolbar__group">
        <button
          className={`btn${filtersOpen || isFiltersActive(filters) ? ' btn--active' : ''}`}
          onClick={() => actions.setFiltersOpen(!filtersOpen)}
          title="Фильтры"
        >
          <Icon name="filter" size={14} /> Фильтры
        </button>
        <IconButton
          icon="info"
          title="Легенда"
          active={legendOpen}
          onClick={() => actions.setLegendOpen(!legendOpen)}
        />
      </div>
    </header>
  );
}
