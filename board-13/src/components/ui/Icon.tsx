import { ICONS, FALLBACK_ICON, type IconKey } from '@/data/icons';

interface IconProps {
  readonly name: IconKey;
  readonly size?: number;
  readonly color?: string;
  readonly strokeWidth?: number;
  readonly className?: string;
}

/** Отрисовка иконки из реестра ICONS. Никакой иконочной логики вне data/icons. */
export function Icon({ name, size = 16, color = 'currentColor', strokeWidth = 2, className }: IconProps) {
  const paths = ICONS[name] ?? ICONS[FALLBACK_ICON];
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke={color}
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      {paths.map((d, i) => (
        <path key={i} d={d} />
      ))}
    </svg>
  );
}
