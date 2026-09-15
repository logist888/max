import { useEffect } from 'react';
import { AppStateProvider, useActions } from '@/app/store';
import { Toolbar } from '@/features/toolbar/Toolbar';
import { LayerRail } from '@/features/layers/LayerRail';
import { Canvas } from '@/features/canvas/Canvas';

function Shell() {
  const actions = useActions();

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        actions.setSearchOpen(true);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [actions]);

  return (
    <div className="app">
      <Toolbar />
      <div className="app__body">
        <LayerRail />
        <Canvas />
      </div>
    </div>
  );
}

export function App() {
  return (
    <AppStateProvider>
      <Shell />
    </AppStateProvider>
  );
}
