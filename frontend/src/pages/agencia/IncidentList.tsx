// Lista de incidentes de la consola de agencia: filtros, reloj del SLA y alta de un incidente manual (spec 008).
import { FormEvent, useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import {
  createIncident,
  getClient,
  listClients,
  listIncidents,
  type ClientDetail,
  type Incident,
  type IncidentStatus,
  type TicketPriority,
} from "../../api";
import SlaClock from "../../components/SlaClock";

// Cada cuánto se vuelve a pedir la lista: un incidente abierto por el monitoreo aparece sin recargar
const REFRESH_MS = 10_000;

export const INCIDENT_STATUS_LABELS: Record<IncidentStatus, string> = {
  abierto: "Abierto",
  mitigado: "Mitigado",
  cerrado: "Cerrado",
};

export const INCIDENT_SOURCE_LABELS = { alerta: "Monitoreo", manual: "Manual" } as const;

// El reloj que corre: el de respuesta hasta que alguien toma (o mitiga) el incidente, luego el de solución
export function ActiveClock({ incident }: { incident: Incident }) {
  if (!incident.acknowledged_at && !incident.mitigated_at) {
    return <SlaClock label="Respuesta" start={incident.started_at} due={incident.response_due_at} done={null} />;
  }
  return (
    <SlaClock label="Solución" start={incident.started_at} due={incident.resolution_due_at} done={incident.mitigated_at} />
  );
}

function NewIncidentForm({ clients, onCancel }: { clients: ClientDetail[]; onCancel: () => void }) {
  const navigate = useNavigate();
  const services = clients.flatMap((client) =>
    client.projects.flatMap((project) => project.services.map((service) => ({ client, service }))),
  );
  const [serviceId, setServiceId] = useState<number | "">("");
  const [priority, setPriority] = useState<TicketPriority>("P2");
  const [title, setTitle] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (serviceId === "") {
      setError("Elige el servicio afectado.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const incident = await createIncident({ service_id: serviceId, priority, title });
      navigate(`/agencia/incidentes/${incident.id}`);
    } catch (saveError) {
      setError((saveError as Error).message);
      setSaving(false);
    }
  }

  return (
    <form className="card stacked-form" onSubmit={handleSubmit} aria-label="Nuevo incidente">
      <h2>Nuevo incidente</h2>
      <p className="muted">Para una falla que el monitoreo no detecta. El reloj del SLA arranca al guardarlo.</p>
      {error && (
        <p className="error" role="alert">
          ✕ {error}
        </p>
      )}
      <label>
        Servicio
        <select value={serviceId} onChange={(event) => setServiceId(event.target.value === "" ? "" : Number(event.target.value))} required>
          <option value="">Elige un servicio</option>
          {services.map(({ client, service }) => (
            <option key={service.id} value={service.id}>
              {client.name} · {service.name}
            </option>
          ))}
        </select>
      </label>
      <label>
        Prioridad
        <select value={priority} onChange={(event) => setPriority(event.target.value as TicketPriority)}>
          <option value="P1">P1 · crítica</option>
          <option value="P2">P2 · alta</option>
          <option value="P3">P3 · media</option>
          <option value="P4">P4 · baja</option>
        </select>
      </label>
      <label>
        Qué pasa
        <input value={title} onChange={(event) => setTitle(event.target.value)} maxLength={200} required />
      </label>
      <div className="form-actions">
        <button type="submit" className="button" disabled={saving}>
          {saving ? "Guardando…" : "Abrir incidente"}
        </button>
        <button type="button" className="button button-secondary" onClick={onCancel}>
          Cancelar
        </button>
      </div>
    </form>
  );
}

export default function IncidentList() {
  const [clients, setClients] = useState<ClientDetail[]>([]);
  const [incidents, setIncidents] = useState<Incident[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<IncidentStatus | "">("");
  const [clientFilter, setClientFilter] = useState<number | "">("");
  const [priorityFilter, setPriorityFilter] = useState<TicketPriority | "">("");
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    listClients()
      .then((list) => Promise.all(list.map((client) => getClient(client.id))))
      .then(setClients)
      .catch((loadError: Error) => setError(loadError.message));
  }, []);

  const load = useCallback(() => {
    listIncidents({
      status: statusFilter || undefined,
      client_id: clientFilter || undefined,
      priority: priorityFilter || undefined,
    })
      .then((data) => {
        setIncidents(data);
        setError(null);
      })
      .catch((loadError: Error) => setError(loadError.message));
  }, [clientFilter, priorityFilter, statusFilter]);

  useEffect(() => {
    load();
    const timer = window.setInterval(load, REFRESH_MS);
    return () => window.clearInterval(timer);
  }, [load]);

  return (
    <>
      <div className="page-header">
        <h1>Incidentes</h1>
        {!creating && (
          <button type="button" className="button button-primary" onClick={() => setCreating(true)}>
            Nuevo incidente
          </button>
        )}
      </div>

      {creating && <NewIncidentForm clients={clients} onCancel={() => setCreating(false)} />}

      {error && (
        <p className="error" role="alert">
          ✕ No se pudieron cargar los incidentes: {error}
        </p>
      )}

      <div className="filters-panel card">
        <div className="filters-grid">
          <label>
            <span>Estado</span>
            <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value as IncidentStatus | "")}>
              <option value="">Todos</option>
              <option value="abierto">Abierto</option>
              <option value="mitigado">Mitigado</option>
              <option value="cerrado">Cerrado</option>
            </select>
          </label>
          <label>
            <span>Cliente</span>
            <select value={clientFilter} onChange={(event) => setClientFilter(event.target.value === "" ? "" : Number(event.target.value))}>
              <option value="">Todos</option>
              {clients.map((client) => (
                <option key={client.id} value={client.id}>
                  {client.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>Prioridad</span>
            <select value={priorityFilter} onChange={(event) => setPriorityFilter(event.target.value as TicketPriority | "")}>
              <option value="">Todas</option>
              <option value="P1">P1</option>
              <option value="P2">P2</option>
              <option value="P3">P3</option>
              <option value="P4">P4</option>
            </select>
          </label>
        </div>
      </div>

      {incidents === null && !error && <p>Cargando incidentes…</p>}
      {incidents !== null && incidents.length === 0 && <p>No hay incidentes con esos filtros.</p>}
      {incidents !== null && incidents.length > 0 && (
        <table className="table">
          <thead>
            <tr>
              <th>Prioridad</th>
              <th>Cliente</th>
              <th>Incidente</th>
              <th>Estado</th>
              <th>Reloj del SLA</th>
            </tr>
          </thead>
          <tbody>
            {incidents.map((incident) => (
              <tr key={incident.id}>
                <td>
                  <span className={`priority-badge priority-${incident.priority}`}>{incident.priority}</span>
                </td>
                <td>
                  <strong>{incident.client_name}</strong>
                  <div className="muted">{incident.service_name}</div>
                </td>
                <td>
                  <Link to={`/agencia/incidentes/${incident.id}`}>
                    <strong>{incident.title}</strong>
                  </Link>
                  <div className="muted">
                    #{incident.id} · {INCIDENT_SOURCE_LABELS[incident.source]}
                  </div>
                </td>
                <td>
                  <span className={`status-pill status-${incident.status}`}>{INCIDENT_STATUS_LABELS[incident.status]}</span>
                </td>
                <td>
                  <ActiveClock incident={incident} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  );
}
