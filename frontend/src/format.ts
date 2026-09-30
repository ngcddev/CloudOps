// Funciones para mostrar datos del Hub en español (tiempos, porcentajes, horarios y precios).
import type { Template } from "./api";

// Minutos → texto corto: 15 → "15 min", 240 → "4 h", 90 → "1 h 30 min"
export function formatMinutes(minutes: number): string {
  if (minutes < 60) return `${minutes} min`;
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  return rest ? `${hours} h ${rest} min` : `${hours} h`;
}

// Porcentaje con coma decimal y al menos un decimal: 99.9 → "99,9 %", 99 → "99,0 %"
export function formatPercent(value: number): string {
  return `${value.toLocaleString("es-CO", { minimumFractionDigits: 1 })} %`;
}

// Horario de atención del plan: "lun-vie 08:00-18:00" → "Lun–Vie 8:00–18:00", "24x7" → "24/7"
export function formatSupportHours(value: string): string {
  if (value === "24x7") return "24/7";
  const match = value.match(/^(\w+)-(\w+) (\d{2}):(\d{2})-(\d{2}):(\d{2})$/);
  if (!match) return value;
  const [, from, to, h1, m1, h2, m2] = match;
  const day = (d: string) => d.charAt(0).toUpperCase() + d.slice(1);
  return `${day(from)}–${day(to)} ${Number(h1)}:${m1}–${Number(h2)}:${m2}`;
}

// Cuándo corre el reloj del SLA de una prioridad
export function formatSlaClock(clock: string): string {
  if (clock === "24x7") return "24/7";
  if (clock === "horario_plan") return "En el horario del plan";
  return clock;
}

// Precio mensual en pesos; null significa que la spec 000 aún no lo define
export function formatPrice(value: number | null): string {
  if (value === null) return "Por definir";
  return value.toLocaleString("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 });
}

export function formatTemplate(template: Template): string {
  return template === "landing_form" ? "Landing + formulario" : "Landing estática";
}
