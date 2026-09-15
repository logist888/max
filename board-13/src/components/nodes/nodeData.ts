import type { Cell, ContractorTemplate, DomainEntity, LayerId } from '@/types';

/** Общие визуальные флаги, вычисляемые графом из состояния (селект/подсветка/фильтр). */
export interface CommonNodeData {
  readonly dimmed: boolean;
  readonly sel: boolean;
  readonly rel: boolean;
}

export interface EntityNodeData extends CommonNodeData {
  readonly entity: DomainEntity;
}
export interface CellNodeData extends CommonNodeData {
  readonly entity: Cell;
}
export interface ContractorNodeData extends CommonNodeData {
  readonly entity: ContractorTemplate;
}
export interface LayerNodeData extends CommonNodeData {
  readonly layerId: LayerId;
  readonly count: number;
}
