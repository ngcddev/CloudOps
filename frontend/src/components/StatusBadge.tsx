// Estado de un servicio con ícono y texto del glosario (el estado nunca se comunica con color).
import type { ServiceStatus } from "../api";

const labels: Record<ServiceStatus, { icon: string; text: string }> = {
  operativo: { icon: "✓", text: "Operativo" },
  degradado: { icon: "!", text: "Con fallas" },
  caido: { icon: "✕", text: "No disponible" },
};

export default function StatusBadge({ status }: { status: ServiceStatus }) {
  const { icon, text } = labels[status];
  return (
    <span className={`status status-${status}`}>
      <span aria-hidden="true">{icon}</span> {text}
    </span>
  );
}
