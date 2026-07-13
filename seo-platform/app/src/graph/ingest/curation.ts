// Ингест курируемых связей направление→профессия из config/graph/curation.json.
// Этой связи нет авторитетно ни в одном источнике (аудит §3). Поэтому:
// method=curated, status=гипотеза, confidence≤0.8 — на страницах показывается
// ТОЛЬКО как помеченное сопоставление, никогда как факт.

import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import type { Staged } from './index.ts';
import { SRC, edge, prov } from './helpers.ts';

interface LeadsTo {
  okso: string; occupationIsco: string; confidence: number;
  curator?: string; curatedAt?: string; note: string;
}

export function ingestCuration(ctx: { appDir: string }): Staged {
  const cfg = JSON.parse(readFileSync(join(ctx.appDir, 'config/graph/curation.json'), 'utf8')) as { leadsTo: LeadsTo[] };
  const edges = (cfg.leadsTo ?? []).map((l) => edge({
    type: 'LEADS_TO',
    from: `me:educationdirection:${l.okso}`,
    to: `me:occupation:${l.occupationIsco}`,
    weight: null, confidence: Math.min(l.confidence, 0.8),
    method: 'curated', status: 'гипотеза',
    provenance: [prov(SRC.curated, `${l.okso}->${l.occupationIsco}`)],
    explanation: l.note,
  }));
  return { nodes: [], edges, sources: edges.length ? [{ source: 'Курируемые связи направление→профессия', records: edges.length }] : [] };
}
