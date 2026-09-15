import type { ReactNode } from 'react';
import { Handle, Position } from '@xyflow/react';

interface NodeFrameProps {
  readonly accent?: string;
  readonly className?: string;
  readonly sel: boolean;
  readonly rel: boolean;
  readonly dimmed: boolean;
  readonly children: ReactNode;
}

/** Внешняя рамка узла: невидимые handle сверху/снизу, акцент-полоса, состояния. */
export function NodeFrame({ accent, className, sel, rel, dimmed, children }: NodeFrameProps) {
  const cls = ['node', className, sel && 'node--selected', rel && !sel && 'node--related', dimmed && 'node--dimmed']
    .filter(Boolean)
    .join(' ');
  return (
    <div className={cls}>
      <Handle type="target" position={Position.Top} isConnectable={false} />
      {accent ? <div className="node__accent" style={{ background: accent }} /> : null}
      {children}
      <Handle type="source" position={Position.Bottom} isConnectable={false} />
    </div>
  );
}
