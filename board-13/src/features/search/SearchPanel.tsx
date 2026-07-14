import { useEffect, useMemo, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { useActions, useAppState } from '@/app/store';
import { searchEntities } from '@/utils/search';
import { presentEntity } from '@/utils/present';
import { KIND_LABEL } from '@/data/labels';
import { Icon } from '@/components/ui/Icon';

/** Поиск по кодам, названиям, типам, каналам, рынкам, CELL, Landing, Event, Decision, Rule. */
export function SearchPanel() {
  const { searchQuery } = useAppState();
  const actions = useActions();
  const inputRef = useRef<HTMLInputElement>(null);
  const [active, setActive] = useState(0);

  const results = useMemo(() => searchEntities(searchQuery), [searchQuery]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);
  useEffect(() => {
    setActive(0);
  }, [searchQuery]);

  const choose = (index: number) => {
    const hit = results[index];
    if (hit) actions.focus(hit.entity.id);
  };

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') actions.setSearchOpen(false);
    else if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActive((a) => Math.min(a + 1, results.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActive((a) => Math.max(a - 1, 0));
    } else if (e.key === 'Enter') {
      choose(active);
    }
  };

  return (
    <div className="search-overlay" onClick={() => actions.setSearchOpen(false)}>
      <motion.div
        className="panel search"
        initial={{ y: -12, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.16 }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="search__input-wrap">
          <Icon name="search" size={18} color="#94a3b8" />
          <input
            ref={inputRef}
            className="search__input"
            placeholder="Поиск: MK_, PG_, CELL_, событие, решение, правило, рынок…"
            value={searchQuery}
            onChange={(e) => actions.setSearch(e.target.value)}
            onKeyDown={onKeyDown}
          />
          <span className="search__kbd">esc</span>
        </div>
        <div className="search__results">
          {searchQuery.trim() === '' ? (
            <div className="search__hint">
              Начните вводить код или название. Ищет по всем сущностям семи слоёв.
            </div>
          ) : results.length === 0 ? (
            <div className="search__hint">Ничего не найдено по запросу «{searchQuery}».</div>
          ) : (
            results.map((r, i) => {
              const { iconKey, color } = presentEntity(r.entity);
              return (
                <div
                  key={r.entity.id}
                  className={`search__result${i === active ? ' search__result--active' : ''}`}
                  onMouseEnter={() => setActive(i)}
                  onClick={() => choose(i)}
                >
                  <span className="node__icon" style={{ background: color.soft, color: color.accent, width: 24, height: 24 }}>
                    <Icon name={iconKey} size={13} />
                  </span>
                  <div style={{ minWidth: 0, flex: 1 }}>
                    <div className="node__name" style={{ fontSize: 13 }}>{r.entity.name}</div>
                    <div className="node__code">{r.entity.code}</div>
                  </div>
                  <span className="chip">{KIND_LABEL[r.entity.kind]}</span>
                </div>
              );
            })
          )}
        </div>
      </motion.div>
    </div>
  );
}
