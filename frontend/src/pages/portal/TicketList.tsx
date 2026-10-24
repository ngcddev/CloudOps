import { useEffect, useMemo, useState } from "react";

import { useAuth } from "../../auth";
import {
  createTicket,
  getClient,
  listTickets,
  type ClientDetail,
  type Ticket,
  type TicketKind,
} from "../../api";

export default function PortalTicketList() {
  // El portal muestra siempre la empresa de quien entró: ya no se elige el cliente (spec 007)
  const { user } = useAuth();
  const clientId = user?.client_id ?? null;
  const [client, setClient] = useState<ClientDetail | null>(null);
  const [selectedServiceId, setSelectedServiceId] = useState<number | "">("");
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [form, setForm] = useState({ title: "", description: "", kind: "solicitud" as TicketKind });
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    if (clientId === null) {
      setError("Tu usuario no tiene una empresa asignada.");
      return;
    }
    getClient(clientId)
      .then(setClient)
      .catch((loadError: Error) => setError(loadError.message));
    listTickets()
      .then(setTickets)
      .catch((loadError: Error) => setError(loadError.message));
  }, [clientId]);

  const services = useMemo(() => client?.projects.flatMap((project) => project.services) ?? [], [client]);

  useEffect(() => {
    setSelectedServiceId((current) => {
      if (services.length === 0) return "";
      return current === "" || !services.some((service) => service.id === current) ? services[0].id : current;
    });
  }, [services]);

  async function handleCreateTicket(event: React.FormEvent) {
    event.preventDefault();
    if (!selectedServiceId) {
      setError("Debes seleccionar un servicio para crear la solicitud.");
      return;
    }

    try {
      setError(null);
      setNotice(null);
      await createTicket({
        service_id: Number(selectedServiceId),
        title: form.title.trim(),
        description: form.description.trim(),
        kind: form.kind,
      });
      const refreshed = await listTickets();
      setTickets(refreshed);
      setForm({ title: "", description: "", kind: "solicitud" });
      setNotice("Solicitud creada correctamente.");
    } catch (submitError) {
      setError((submitError as Error).message);
    }
  }

  return (
    <>
      <div className="page-header">
        <h1>Solicitudes</h1>
        {client && <p className="muted">{client.name}</p>}
      </div>

      {error && (
        <p className="error" role="alert">
          ✕ {error}
        </p>
      )}
      {notice && (
        <p className="notice" role="status">
          ✓ {notice}
        </p>
      )}

      <section className="card portal-form">
        <h2>Nueva solicitud</h2>
        <form onSubmit={handleCreateTicket} className="stacked-form">
          <label>
            <span>Servicio</span>
            <select value={selectedServiceId} onChange={(event) => setSelectedServiceId(event.target.value === "" ? "" : Number(event.target.value))}>
              {services.map((service) => (
                <option key={service.id} value={service.id}>
                  {service.name} · {service.host}
                </option>
              ))}
            </select>
          </label>

          <label>
            <span>¿Qué necesitas?</span>
            <select
              value={form.kind}
              onChange={(event) => setForm((current) => ({ ...current, kind: event.target.value as TicketKind }))}
            >
              <option value="solicitud">Reportar un problema o hacer una consulta</option>
              <option value="cambio">Pedir un cambio en mi sitio</option>
            </select>
          </label>

          <label>
            <span>Título</span>
            <input
              type="text"
              value={form.title}
              onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))}
              placeholder="Ej. El menú del domingo no aparece"
            />
          </label>

          <label>
            <span>Descripción</span>
            <textarea
              rows={4}
              value={form.description}
              onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))}
              placeholder="Describe qué problema tienes con el servicio."
            />
          </label>

          <button type="submit" className="button">
            Enviar solicitud
          </button>
        </form>
      </section>

      <section className="card">
        <h2>Mis solicitudes</h2>
        {tickets.length === 0 && <p>No tienes solicitudes en este momento.</p>}
        {tickets.length > 0 && (
          <table className="table">
            <thead>
              <tr>
                <th>Solicitud</th>
                <th>Tipo</th>
                <th>Prioridad</th>
                <th>Estado</th>
                <th>Creada</th>
              </tr>
            </thead>
            <tbody>
              {tickets.map((ticket) => (
                <tr key={ticket.id}>
                  <td>
                    <strong>{ticket.title}</strong>
                    <div className="muted">#{ticket.id}</div>
                  </td>
                  <td>{ticket.kind === "cambio" ? "Cambio en el sitio" : "Consulta o problema"}</td>
                  <td>
                    <span className={`priority-badge priority-${ticket.priority ?? "sin-prioridad"}`}>{ticket.priority ?? "—"}</span>
                  </td>
                  <td>
                    <span className={`status-pill status-${ticket.status}`}>{ticket.status}</span>
                  </td>
                  <td>{new Date(ticket.created_at).toLocaleDateString("es-CO")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </>
  );
}
