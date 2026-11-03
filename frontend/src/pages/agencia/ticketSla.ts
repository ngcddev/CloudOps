// Estado del SLA de una solicitud tal como lo muestran la bandeja y el detalle de la agencia (spec 004).
import type { Ticket } from "../../api";

// `sin_plazo` es una solicitud que aún no se clasifica: todavía no tiene fechas límite que vencer.
export type SlaState = "sin_plazo" | "a_tiempo" | "en_riesgo" | "vencido";

export const SLA_LABELS: Record<SlaState, string> = {
  sin_plazo: "sin plazo",
  a_tiempo: "a tiempo",
  en_riesgo: "en riesgo",
  vencido: "vencido",
};

export const SLA_ICONS: Record<SlaState, string> = {
  sin_plazo: "–",
  a_tiempo: "✓",
  en_riesgo: "⚠",
  vencido: "✕",
};

export function getTicketSlaState(ticket: Ticket): SlaState {
  const createdAt = new Date(ticket.created_at).getTime();
  const dueIso = ticket.first_response_at
    ? ticket.resolution_due_at ?? ticket.response_due_at
    : ticket.response_due_at ?? ticket.resolution_due_at;
  // Sin clasificar no hay fecha límite: no se puede estar vencido
  if (!dueIso) return "sin_plazo";

  const dueAt = new Date(dueIso).getTime();
  if (!Number.isFinite(dueAt) || dueAt <= 0) return "sin_plazo";

  const now = Date.now();
  if (now >= dueAt) return "vencido";

  const totalWindow = dueAt - createdAt;
  const elapsed = now - createdAt;
  if (totalWindow > 0 && elapsed * 5 >= totalWindow * 4) return "en_riesgo";

  return "a_tiempo";
}
