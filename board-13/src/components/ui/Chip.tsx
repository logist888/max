interface ChipProps {
  readonly label: string;
  readonly color?: string;
  readonly dot?: boolean;
  readonly on?: boolean;
  readonly interactive?: boolean;
  readonly title?: string;
  readonly onClick?: () => void;
}

/** Универсальная пилюля-метка. Цвет приходит извне — компонент не знает предметной области. */
export function Chip({ label, color, dot, on, interactive, title, onClick }: ChipProps) {
  const cls = ['chip', dot && 'chip--dot', interactive && 'chip--interactive', on && 'chip--on']
    .filter(Boolean)
    .join(' ');
  return (
    <span
      className={cls}
      title={title ?? label}
      onClick={interactive ? onClick : undefined}
      style={color && !on ? { color } : undefined}
      role={interactive ? 'button' : undefined}
    >
      {label}
    </span>
  );
}
