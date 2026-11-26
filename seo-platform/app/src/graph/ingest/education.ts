// Ингест образовательного слоя из витрин конвейера (build/*.json).
// Зависит от `npm run pipeline` (витрины должны быть собраны). Направление —
// авторитетно из снимка ВУЗ-навигатора. УГСН держим как атрибут направления
// (группировка — забота существующего сайта /specialnosti/), отдельным узлом
// пока не заводим.

import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import type { Staged } from './index.ts';
import { SRC, node, prov } from './helpers.ts';

interface DirectionAgg {
  okso: string; slug: string; name: string; level: string; ugsCode: string;
  scientific: boolean; orgCount: number; cityCount: number;
}

export function ingestEducation(ctx: { appDir: string }): Staged {
  const build = join(ctx.appDir, 'build');
  const directions = JSON.parse(readFileSync(join(build, 'directions.json'), 'utf8')) as DirectionAgg[];

  const nodes = directions.map((d) => node({
    type: 'EducationDirection', key: d.okso,
    localIds: [{ scheme: 'okso', value: d.okso }],
    labels: { ru: d.name },
    status: 'факт', confidence: 0.98,
    provenance: [prov(SRC.edu, d.okso)],
    attrs: {
      slug: d.slug, level: d.level, ugsCode: d.ugsCode,
      scientific: d.scientific, orgCount: d.orgCount, cityCount: d.cityCount,
    },
  }));

  return { nodes, edges: [], sources: [{ source: 'Направления (ОКСО, витрины)', records: directions.length }] };
}
