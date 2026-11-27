// Íconos de los campos propios (selector, fecha y mes): flecha, marca de elegido, calendario y flechas de navegación. Heredan el color del texto y no se leen en voz alta.
import type { ReactNode } from "react";

function Icon({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <svg
      className={className}
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      {children}
    </svg>
  );
}

export function ArrowIcon() {
  return (
    <Icon className="campo-flecha">
      <path d="M4 6.5 8 10.5 12 6.5" />
    </Icon>
  );
}

export function CheckIcon() {
  return (
    <Icon className="campo-check">
      <path d="M3.5 8.5 6.5 11.5 12.5 4.5" />
    </Icon>
  );
}

export function CalendarIcon() {
  return (
    <Icon className="campo-icono">
      <rect x="2.5" y="3.5" width="11" height="10" rx="1.5" />
      <path d="M2.5 6.5h11M5.5 2v3M10.5 2v3" />
    </Icon>
  );
}

export function ChevronLeft() {
  return (
    <Icon>
      <path d="M10 3.5 5.5 8 10 12.5" />
    </Icon>
  );
}

export function ChevronRight() {
  return (
    <Icon>
      <path d="M6 3.5 10.5 8 6 12.5" />
    </Icon>
  );
}
