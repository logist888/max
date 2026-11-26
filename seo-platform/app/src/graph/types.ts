// Career Knowledge Graph — канонические типы узла и связи.
//
// Конверт провенанса — та же дисциплина, что в pipeline/types.ts
// («пропуск = null, никогда не 0 и не выдуманное значение») и во frontmatter
// vault (status: факт | гипотеза | требует-проверки). Принцип: ни одна
// неуверенная связь не удаляется — она помечается method + confidence и
// фильтруется на выходе. Публичная страница показывает как факт только
// authoritative (и проверенный crosswalk); curated/inferred — как помеченную
// гипотезу; где связи нет — «Информация отсутствует».

export type Method = 'authoritative' | 'crosswalk' | 'inferred' | 'curated';
export type Status = 'факт' | 'гипотеза' | 'требует-проверки';

export interface Provenance {
  /** Человекочитаемый код источника: «ESCO v1.2.1», «O*NET 30.3», «ОКЗ ОК 010-2014». */
  source: string;
  /** Идентификатор записи в источнике (URI ESCO, код ОКСО, SOC, код профстандарта). */
  sourceId?: string;
  sourceUrl?: string;
  /** Дата публикации источника (не дата загрузки). */
  sourceDate?: string;
  /** Код лицензии из config/graph/licenses.json. */
  license: string;
  method: Method;
  /** Когда мы забрали данные (для старения real-time фактов, напр. hh.ru). */
  retrievedAt?: string;
}

export type NodeType =
  | 'Country' | 'EducationSystem' | 'University' | 'Faculty'
  | 'EducationDirection' | 'EducationProgram' | 'ProgramProfile'
  | 'Qualification' | 'Competency' | 'Knowledge' | 'Skill' | 'Tool' | 'Technology'
  | 'Occupation' | 'JobRole' | 'Industry' | 'Employer' | 'ProfessionalStandard'
  | 'CareerOutcome' | 'CareerTransition' | 'LearningResource'
  | 'Certification' | 'License' | 'Assessment' | 'Salary' | 'LabourMarket';

/** Локальный идентификатор в системе-источнике (scheme: okso|isco08|esco|onet-soc|okz|profstandard|hh-role|…). */
export interface LocalId { scheme: string; value: string; }

export interface GraphNode {
  /** Global ID, URN: me:<type-lowercase>:<key>. Детерминирован из стабильного ключа. */
  id: string;
  type: NodeType;
  localIds: LocalId[];
  /** Метки по языкам. labels.ru обязательна для публичного вывода; если русского
   *  авторитетного названия нет — держим en и ставим status требует-проверки. */
  labels: { ru?: string; en?: string; [lang: string]: string | undefined };
  status: Status;
  /** Доверие к самому узлу, 0..1. */
  confidence: number;
  /** Дата, на которую утверждение верно (ISO). */
  validAsOf: string;
  provenance: Provenance[];
  version: number;
  /** Полезная нагрузка, зависящая от типа. */
  attrs: Record<string, unknown>;
}

export type EdgeType =
  // Авторитетные (из источника)
  | 'IN_DIRECTION' | 'IN_UGS' | 'OFFERED_AT' | 'IN_CITY' | 'IN_REGION'
  | 'HAS_QUALIFICATION' | 'REQUIRES' | 'GOVERNED_BY' | 'REQUIRES_LICENSE'
  | 'EMPLOYED_BY' | 'HAS_SALARY' | 'IN_LABOURMARKET'
  // Кроссволк (через ISCO-мост)
  | 'ISCO_MAPS' | 'CROSSWALK_EQUIV' | 'ANALOG_OF'
  // Курируемые / выводимые — НИКОГДА не факт в публичном выводе
  | 'LEADS_TO' | 'DEVELOPS' | 'TRANSITIONS_TO' | 'INDICATES'
  // Служебные / агрегирующие
  | 'AGGREGATES' | 'TAUGHT_BY' | 'CERTIFIED_BY' | 'RELATED_TO';

export interface GraphEdge {
  /** Детерминированный id: me:edge:<from>--<TYPE>--<to>. */
  id: string;
  type: EdgeType;
  from: string;
  to: string;
  direction: 'directed' | 'undirected';
  /** Сила/релевантность связи (essential ≫ optional и т.п.), 0..1 или null. */
  weight: number | null;
  /** Вероятность (только для переходов/склонностей), 0..1 или null. */
  probability: number | null;
  /** Доверие к самому утверждению связи, 0..1. */
  confidence: number;
  method: Method;
  status: Status;
  provenance: Provenance[];
  /** По-русски, человекочитаемо: почему связь существует (для отчёта и UI). */
  explanation: string;
  validAsOf: string;
  createdAt: string;
}

/** Артефакт графа = два потока JSONL + манифест сборки. */
export interface GraphManifest {
  builtAt: string;
  runId: string;
  sources: { source: string; localFile?: string; sha256?: string; records?: number }[];
  counts: { nodes: number; edges: number; byNodeType: Record<string, number>; byEdgeType: Record<string, number> };
}
