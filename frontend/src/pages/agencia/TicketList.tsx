import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import {
  getClient,
  listClients,
  listTickets,
  type ClientDetail,
  type Ticket,
  type TicketPriority,
  type TicketStatus,
} from "../../api";
import { getTicketSlaState, SLA_ICONS, SLA_LABELS, type SlaState } from "./ticketSla";

function findTicketClient(ticket: Ticket, clients: ClientDetail[]): ClientDetail | undefined {
  return clients.find((client) =>
    client.projects.some((project) => project.services.some((service) => service.id === ticket.service_id)),
  );
}

function findTicketService(ticket: Ticket, clients: ClientDetail[]): { clientName: string; serviceName: string } | null {
  const client = findTicketClient(ticket, clients);
  if (!client) return null;

  const service = client.projects.flatMap((project) => project.services).find((item) => item.id === ticket.service_id);
  if (!service) return null;

  return {
    clientName: client.name,
    serviceName: service.name,
  };
}

export default function TicketList() {
  const [clients, setClients] = useState<ClientDetail[]>([]);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [clientFilter, setClientFilter] = useState<number | "">("");
  const [priorityFilter, setPriorityFilter] = useState<TicketPriority | "">("");
  const [statusFilter, setStatusFilter] = useState<TicketStatus | "">("");
  const [slaFilter, setSlaFilter] = useState<SlaState | "">("");

  useEffect(() => {
    Promise.all([listClients(), listTickets()])
      .then(async ([clientList, ticketData]) => {
        const clientDetails = await Promise.all(clientList.map((client) => getClient(client.id)));
        setClients(clientDetails);
        setTickets(ticketData);
      })
      .catch((loadError: Error) => setError(loadError.message));
  }, []);

  const visibleTickets = useMemo(() => {
    return tickets.filter((ticket) => {
      const matchesClient = clientFilter === "" || findTicketClient(ticket, clients)?.id === clientFilter;
      const matchesPriority = priorityFilter === "" || ticket.priority === priorityFilter;
      const matchesStatus = statusFilter === "" || ticket.status === statusFilter;
      const matchesSla = slaFilter === "" || getTicketSlaState(ticket) === slaFilter;
      return matchesClient && matchesPriority && matchesStatus && matchesSla;
    });
  }, [clientFilter, clients, priorityFilter, slaFilter, statusFilter, tickets]);

  return (
    <>
      <div className="page-header">
        <h1>Solicitudes</h1>
      </div>

      {error && (
        <p className="error" role="alert">
          ✕ No se pudo cargar la bandeja: {error}
        </p>
      )}

      {!error && (
        <div className="filters-panel card">
          <div className="filters-grid">
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

            <label>
              <span>Estado</span>
              <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value as TicketStatus | "")}>
                <option value="">Todos</option>
                <option value="abierto">Abierto</option>
                <option value="en_progreso">En progreso</option>
                <option value="en_espera">En espera</option>
                <option value="resuelto">Resuelto</option>
                <option value="cerrado">Cerrado</option>
              </select>
            </label>

            <label>
              <span>SLA</span>
              <select value={slaFilter} onChange={(event) => setSlaFilter(event.target.value as SlaState | "")}>
                <option value="">Todos</option>
                <option value="sin_plazo">Sin plazo</option>
                <option value="a_tiempo">A tiempo</option>
                <option value="en_riesgo">En riesgo</option>
                <option value="vencido">Vencido</option>
              </select>
            </label>
          </div>
        </div>
      )}

      {!error && (
        <>
          {visibleTickets.length === 0 ? (
            <p>No hay solicitudes con esos filtros.</p>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>Cliente</th>
                  <th>Solicitud</th>
                  <th>Prioridad</th>
                  <th>Estado</th>
                  <th>SLA</th>
                </tr>
              </thead>
              <tbody>
                {visibleTickets.map((ticket) => {
                  const service = findTicketService(ticket, clients);
                  const slaState = getTicketSlaState(ticket);
                  return (
                    <tr key={ticket.id}>
                      <td>
                        <strong>{service?.clientName ?? "Cliente"}</strong>
                        <div className="muted">{service?.serviceName ?? "Servicio"}</div>
                      </td>
                      <td>
                        <Link to={`/agencia/tickets/${ticket.id}`}>
                          <strong>{ticket.title}</strong>
                        </Link>
                        <div className="muted">#{ticket.id}</div>
                      </td>
                      <td>
                        <span className={`priority-badge priority-${ticket.priority ?? "sin-prioridad"}`}>{ticket.priority ?? "sin asignar aún"}</span>
                      </td>
                      <td>
                        <span className={`status-pill status-${ticket.status}`}>{ticket.status}</span>
                      </td>
                      <td>
                        <span className={`sla-badge sla-${slaState}`}>
                          {SLA_ICONS[slaState]} {SLA_LABELS[slaState]}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </>
      )}
    </>
  );
}
