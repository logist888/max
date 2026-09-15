import type { ContractorTemplate } from '@/types';

/**
 * Слой CONTRACTOR — шаблон ТЗ подрядчику (блок Д.3), собирается за 15 минут.
 * Пример заполнен на ячейке CELL_VK_QUIZ_RU_01. Разворачивает ячейку → эдж contractor_instantiates.
 * Источник: docs/12-traffic-platform-decisions.md, блок Д.3.
 */
export const CONTRACTORS: readonly ContractorTemplate[] = [
  {
    id: 'contractor_template', kind: 'contractor', layer: 'contractor', code: 'ТЗ',
    name: 'ТЗ подрядчику на закупку трафика',
    description: 'Шаблон запуска ячейки: канал, посадочная, UTM, бюджет, KPI, запреты, отчётность, стоп-правило.',
    fields: [
      { key: 'channel', label: '1. Канал (MK_)', value: 'MK_VK_ADS (Таргет VK)' },
      { key: 'market', label: '2. Рынок', value: 'СНГ' },
      { key: 'cell', label: '3. Ячейка (CELL_)', value: 'CELL_VK_QUIZ_RU_01' },
      { key: 'landing', label: '4. Посадочная', value: 'URL /quiz · ключ PG_QUIZ' },
      { key: 'action', label: '5. Целевое действие', value: 'EVT_SCREENING_DONE (измеримо в системе)' },
      { key: 'utm', label: '6. UTM-шаблон', value: 'utm_source=vk_ads&utm_medium=cpc&utm_campaign=CELL_VK_QUIZ_RU_01&utm_content=<creative>', note: 'для MK_REF_*: &ref_id=<REF_>' },
      { key: 'budget', label: '7. Бюджет', value: 'не менее $400 на ячейку' },
      { key: 'kpi', label: '8. KPI и градация', value: 'CPL: ≤ $3 зел / $3–6 жёлт / > $6 красн [ЦЕЛЬ] · CR пос.: ≥ 40% зел / 25–40% жёлт / < 25% красн', note: 'ДРР считает заказчик по сшивке; подрядчик — до CPL/CR посадочной' },
    ],
    prohibitions: [
      'НЕ менять посадочную (смена = новая ячейка)',
      'НЕ лить на главную (PG_HOME)',
      'НЕ вести холодный трафик на карточку LST_DIAG_*',
      'НЕ упоминать названия методик (BFAS/RIASEC и пр.) — только рабочие',
      'Соблюдать «одна кампания — одна посадочная»',
    ],
    reporting: 'Ежедневно (расход, CPL) + еженедельно (CR посадочной)',
    stopRule: 'Бюджет ячейки исчерпан при CPL > красного и 0 заказов → СТОП, разбор (креатив / посадочная / канал)',
  },
];
