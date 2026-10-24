// Bitácora: quién hizo qué y cuándo, con filtros por usuario, objeto, acción y fechas (spec 007, T19).
import { useCallback, useEffect, useState } from "react";

import { listAuditLogs, type AuditLog, type AuditLogFilters } from "../../api";
import { formatDateTime } from "../../format";

// Etiquetas en español; si llega un valor nuevo (de una spec posterior) se muestra tal cual
const ENTITY_LABELS: Record<string, string> = {
  ticket: "Solicitud",
  client: "Cliente",
  change_request: "Cambio de versión",
  incident: "Incidente",
};

const ACTION_LABELS: Record<string, string> = {
  cambiar_prioridad: "Cambió la prioridad",
  asignar: "Asignó responsable",
  cambiar_estado: "Cambió el estado",
  crear: "Creó",
  editar: "Editó",
  aprobar: "Aprobó",
  rechazar: "Rechazó",
  desplegar: "Publicó",
  fallar: "No se pudo publicar",
};

// Las fechas del filtro son días de Colombia (UTC-5, sin horario de verano)
const startOfDay = (day: string) => new Date(`${day}T00:00:00-05:00`).toISOString();
const endOfDay = (day: string) => new Date(`${day}T23:59:59-05:00`).toISOString();

// Nombre en español de cada dato del detalle; los desconocidos se muestran con su nombre tal cual
const DETAIL_LABELS: Record<string, string> = {
  de: "Antes",
  a: "Ahora",
  motivo: "Motivo",
  commit: "Commit",
  name: "Nombre",
  campos: "Campos",
  ticket_id: "Solicitud",
  sincronizacion: "Sincronización",
  salud: "Salud",
};

function describe(details: AuditLog["details"]): string {
  if (!details) return "—";
  const text = Object.entries(details)
    .filter(([, value]) => value !== null && value !== undefined && value !== "")
    .map(([key, value]) => `${DETAIL_LABELS[key] ?? key}: ${Array.isArray(value) ? value.join(", ") : String(value)}`)
    .join(" · ");
  return text || "—";
}

export default function AuditLogList() {
  const [logs, setLogs] = useState<AuditLog[] | null>(null);
  const [people, setPeople] = useState<{ id: number; name: string }[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState({ user: "", entity: "", action: "", from: "", to: "" });

  const load = useCallback(async () => {
    const query: AuditLogFilters = {};
    if (filters.user) query.user_id = Number(filters.user);
    if (filters.entity) query.entity = filters.entity;
    if (filters.action) query.action = filters.action;
    if (filters.from) query.from = startOfDay(filters.from);
    if (filters.to) query.to = endOfDay(filters.to);
    try {
      const result = await listAuditLogs(query);
      setLogs(result);
      setError(null);
      // Las personas del filtro salen de lo que ya hay en la bitácora, sin pedir otra lista
      setPeople((known) => {
        const byId = new Map(known.map((person) => [person.id, person]));
        for (const log of result) {
          if (log.user_id !== null) byId.set(log.user_id, { id: log.user_id, name: log.user_name });
        }
        return [...byId.values()];
      });
    } catch (loadError) {
      setError((loadError as Error).message);
    }
  }, [filters]);

  useEffect(() => {
    void load();
  }, [load]);

  const set = (field: keyof typeof filters) => (event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setFilters((current) => ({ ...current, [field]: event.target.value }));

  return (
    <>
      <div className="page-header">
        <h1>Bitácora</h1>
        <p className="muted">
          Las acciones sensibles quedan aquí con quién las hizo y cuándo. No se pueden editar ni borrar.
        </p>
      </div>

      {error && (
        <p className="error" role="alert">
          ✕ {error}
        </p>
      )}

      <section className="card filters-panel">
        <div className="filters-grid">
          <label>
            <span>Usuario</span>
            <select value={filters.user} onChange={set("user")}>
              <option value="">Todos</option>
              {people.map((person) => (
                <option key={person.id} value={person.id}>
                  {person.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>Objeto</span>
            <select value={filters.entity} onChange={set("entity")}>
              <option value="">Todos</option>
              {Object.entries(ENTITY_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>Acción</span>
            <select value={filters.action} onChange={set("action")}>
              <option value="">Todas</option>
              {Object.entries(ACTION_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>Desde</span>
            <input type="date" value={filters.from} onChange={set("from")} />
          </label>
          <label>
            <span>Hasta</span>
            <input type="date" value={filters.to} onChange={set("to")} />
          </label>
        </div>
      </section>

      <section className="card">
        {logs === null && !error && <p className="muted">Cargando…</p>}
        {logs !== null && logs.length === 0 && <p>No hay acciones registradas con esos filtros.</p>}
        {logs !== null && logs.length > 0 && (
          <table className="table">
            <thead>
              <tr>
                <th>Fecha (hora de Colombia)</th>
                <th>Usuario</th>
                <th>Acción</th>
                <th>Objeto</th>
                <th>Detalle</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id}>
                  <td>{formatDateTime(log.created_at)}</td>
                  <td>{log.user_name}</td>
                  <td>{ACTION_LABELS[log.action] ?? log.action}</td>
                  <td>
                    {ENTITY_LABELS[log.entity] ?? log.entity}
                    {log.entity_id !== null && <span className="muted"> #{log.entity_id}</span>}
                  </td>
                  <td className="muted">{describe(log.details)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {logs !== null && logs.length === 200 && (
          <p className="muted">Se muestran las 200 acciones más recientes; usa los filtros para acotar.</p>
        )}
      </section>
    </>
  );
}
