// Reloj del SLA de un incidente: cuenta cada segundo hasta la fecha límite y muestra su estado con texto e ícono.
import { useEffect, useState } from "react";

import { clockState, type ClockState } from "../api";
import { formatDateTime } from "../format";

const LABELS: Record<ClockState, { icon: string; text: string }> = {
  a_tiempo: { icon: "◷", text: "a tiempo" },
  en_riesgo: { icon: "!", text: "en riesgo" },
  vencido: { icon: "✗", text: "vencido" },
  cumplido: { icon: "✓", text: "cumplido" },
};

// 754 s → "12:34"; 3 h 2 min → "3:02:00"
function formatDuration(totalSeconds: number): string {
  const seconds = Math.max(0, Math.floor(totalSeconds));
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  const pad = (n: number) => String(n).padStart(2, "0");
  return h > 0 ? `${h}:${pad(m)}:${pad(s)}` : `${m}:${pad(s)}`;
}

interface Props {
  // «Respuesta» o «Solución»
  label: string;
  start: string;
  due: string;
  // Hora en que se cumplió (tomar o mitigar); con ella el reloj queda detenido
  done: string | null;
}

export default function SlaClock({ label, start, due, done }: Props) {
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    if (done) return;
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [done]);

  const state = clockState(start, due, done, now);
  const { icon, text } = LABELS[state];
  const dueMs = Date.parse(due);
  let detail: string;
  if (done) {
    detail = `${state === "cumplido" ? "Cumplido" : "Cumplido tarde"} el ${formatDateTime(done)}`;
  } else if (now < dueMs) {
    detail = `Quedan ${formatDuration((dueMs - now) / 1000)} · vence ${formatDateTime(due)}`;
  } else {
    detail = `Venció hace ${formatDuration((now - dueMs) / 1000)}`;
  }

  return (
    <span className="sla-clock" role="timer" aria-live="off">
      <span className="sla-clock-label">{label}</span>
      <span className={`sla-badge sla-${state}`}>
        <span aria-hidden="true">{icon}</span> {text}
      </span>
      <span className="sla-clock-time">{detail}</span>
    </span>
  );
}
