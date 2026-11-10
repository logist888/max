// Ингест курируемых связей направление→профессия из config/graph/curation.json.
// Этой связи нет авторитетно ни в одном источнике (аудит §3). Поэтому:
// method=curated, status=гипотеза, confidence≤0.8 — на страницах показывается
// ТОЛЬКО как помеченное сопоставление, никогда как факт.
//
// Сопоставление задаётся на уровне УГСН (ugsToOccupations) и распространяется
// на все направления группы (по ugsCode из витрин).

import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import type { Staged } from './index.ts';
import { SRC, edge, prov } from './helpers.ts';

interface OccRef { isco: string; confidence: number; note: string; }
interface DirectionAgg { okso: string; ugsCode: string; name: string; }

export function ingestCuration(ctx: { appDir: string }): Staged {
  const cfg = JSON.parse(readFileSync(join(ctx.appDir, 'config/graph/curation.json'), 'utf8')) as {
    ugsToOccupations?: Record<string, OccRef[]>;
  };
  const directions = JSON.parse(readFileSync(join(ctx.appDir, 'build/directions.json'), 'utf8')) as DirectionAgg[];
  const map = cfg.ugsToOccupations ?? {};

  const edges = [];
  for (const d of directions) {
    const occs = map[d.ugsCode];
    if (!occs) continue;
    for (const o of occs) {
      edges.push(edge({
        type: 'LEADS_TO',
        from: `me:educationdirection:${d.okso}`,
        to: `me:occupation:${o.isco}`,
        weight: null, confidence: Math.min(o.confidence, 0.8),
        method: 'curated', status: 'гипотеза',
        provenance: [prov(SRC.curated, `${d.okso}->${o.isco}`)],
        explanation: `Сопоставление по профилю укрупнённой группы: ${o.note}. Экспертная гипотеза, не официальная связь.`,
      }));
    }
  }
  return { nodes: [], edges, sources: edges.length ? [{ source: 'Курируемые связи направление→профессия (УГСН)', records: edges.length }] : [] };
}
