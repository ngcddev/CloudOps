import { useEffect, useMemo, useState } from "react";

import {
  createTicket,
  getClient,
  listClients,
  listTickets,
  type ClientDetail,
  type Ticket,
} from "../../api";

export default function PortalTicketList() {
  const [clients, setClients] = useState<ClientDetail[]>([]);
  const [selectedClientId, setSelectedClientId] = useState<number | "">("");
  const [selectedServiceId, setSelectedServiceId] = useState<number | "">("");
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [form, setForm] = useState({ title: "", description: "" });
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    listClients()
      .then(async (clientSummaries) => {
        const clientDetails = await Promise.all(clientSummaries.map((client) => getClient(client.id)));
        setClients(clientDetails);
        if (clientDetails.length > 0) {
          setSelectedClientId((current) => (current === "" ? clientDetails[0].id : current));
        }
      })
      .catch((loadError: Error) => setError(loadError.message));
  }, []);

  useEffect(() => {
    if (selectedClientId === "") {
      setTickets([]);
      setSelectedServiceId("");
      return;
    }

    listTickets({ client_id: Number(selectedClientId), viewer_role: "cliente" })
      .then(setTickets)
      .catch((loadError: Error) => setError(loadError.message));
  }, [selectedClientId]);

  const selectedClient = useMemo(
    () => clients.find((client) => client.id === selectedClientId) ?? null,
    [clients, selectedClientId],
  );

  useEffect(() => {
    if (!selectedClient) {
      setSelectedServiceId("");
      return;
    }

    const services = selectedClient.projects.flatMap((project) => project.services);
    if (services.length === 0) {
      setSelectedServiceId("");
      return;
    }

    setSelectedServiceId((current) => {
      if (current === "" || !services.some((service) => service.id === current)) {
        return services[0].id;
      }
      return current;
    });
  }, [selectedClient]);

  async function handleCreateTicket(event: React.FormEvent) {
    event.preventDefault();
    if (!selectedClientId || !selectedServiceId) {
      setError("Debes seleccionar un cliente y servicio para crear la solicitud.");
      return;
    }

    try {
      setError(null);
      setNotice(null);
      await createTicket({
        service_id: Number(selectedServiceId),
        created_by_id: 1,
        title: form.title.trim(),
        description: form.description.trim(),
        kind: "solicitud",
      });
      const refreshed = await listTickets({ client_id: Number(selectedClientId), viewer_role: "cliente" });
      setTickets(refreshed);
      setForm({ title: "", description: "" });
      setNotice("Solicitud creada correctamente.");
    } catch (submitError) {
      setError((submitError as Error).message);
    }
  }

  return (
    <>
      <div className="page-header">
        <h1>Solicitudes</h1>
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
            <span>Cliente</span>
            <select value={selectedClientId} onChange={(event) => setSelectedClientId(event.target.value === "" ? "" : Number(event.target.value))}>
              {clients.map((client) => (
                <option key={client.id} value={client.id}>
                  {client.name}
                </option>
              ))}
            </select>
          </label>

          <label>
            <span>Servicio</span>
            <select value={selectedServiceId} onChange={(event) => setSelectedServiceId(event.target.value === "" ? "" : Number(event.target.value))}>
              {selectedClient?.projects.flatMap((project) => project.services).map((service) => (
                <option key={service.id} value={service.id}>
                  {service.name} · {service.host}
                </option>
              )) ?? null}
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
