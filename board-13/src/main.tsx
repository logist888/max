import React from 'react';
import ReactDOM from 'react-dom/client';
import '@xyflow/react/dist/style.css';
import '@/styles/globals.css';
import { App } from '@/app/App';

const root = document.getElementById('root');
if (!root) throw new Error('Не найден корневой элемент #root');

ReactDOM.createRoot(root).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
