import type { NodeTypes } from '@xyflow/react';
import { EntityNode } from './EntityNode';
import { CellNode } from './CellNode';
import { ContractorNode } from './ContractorNode';
import { LayerGroupNode } from './LayerGroupNode';

/** Реестр типов узлов React Flow. Тип узла выбирается графом по kind сущности. */
export const nodeTypes: NodeTypes = {
  entity: EntityNode,
  cell: CellNode,
  contractor: ContractorNode,
  layer: LayerGroupNode,
};
