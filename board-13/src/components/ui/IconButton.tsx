import { Icon } from './Icon';
import type { IconKey } from '@/data/icons';

interface IconButtonProps {
  readonly icon: IconKey;
  readonly title: string;
  readonly onClick?: () => void;
  readonly active?: boolean;
  readonly ghost?: boolean;
}

export function IconButton({ icon, title, onClick, active, ghost }: IconButtonProps) {
  const cls = ['btn', 'btn--icon', ghost && 'btn--ghost', active && 'btn--active']
    .filter(Boolean)
    .join(' ');
  return (
    <button className={cls} title={title} aria-label={title} onClick={onClick}>
      <Icon name={icon} size={16} />
    </button>
  );
}
