// Inicio del portal del cliente (spec 010, T16): estado del sitio, disponibilidad frente al objetivo,
// fallas del mes y solicitudes. Todo el texto sale de texts/cliente.ts (glosario, CA-4).
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import {
  getClientDashboard,
  listClientIncidents,
  listTickets,
  mesActual,
  type ClientDashboardKpi,
  type ClientIncident,
  type Ticket,
} from "../../api";
import { useAuth } from "../../auth";
import { formatDateTime, formatPercent } from "../../format";
import {
  estadosIncidente,
  estadosSolicitud,
  textoDisponibilidad,
  textoEstado,
  textosCliente,
} from "../../texts/cliente";

function enElMes(iso: string, month: string): boolean {
  return (
    new Intl.DateTimeFormat("en-CA", {
      timeZone: "America/Bogota",
      year: "numeric",
      month: "2-digit",
    })
      .format(new Date(iso))
      .slice(0, 7) === month
  );
}

const ESTADO_ICONO = { operativo: "✓", degradado: "!", caido: "✕" } as const;

export default function PortalHome() {
  const { user } = useAuth();
  const clientId = user?.client_id ?? null;
  const month = mesActual();
  const [dashboard, setDashboard] = useState<ClientDashboardKpi | null>(null);
  const [incidents, setIncidents] = useState<ClientIncident[]>([]);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (clientId === null) {
      setError("Su usuario no está ligado a un cliente.");
      return;
    }
    let cancelled = false;
    Promise.all([
      getClientDashboard(clientId, month),
      listClientIncidents(clientId, month),
      listTickets({ client_id: clientId }),
    ])
      .then(([dashboardData, incidentData, ticketData]) => {
        if (cancelled) return;
        setDashboard(dashboardData);
        setIncidents(incidentData.filter((incident) => enElMes(incident.started_at, month)));
        setTickets(ticketData.filter((ticket) => enElMes(ticket.created_at, month)));
      })
      .catch((e: Error) => {
        if (!cancelled) setError(e.message);
      });
    return () => {
      cancelled = true;
    };
  }, [clientId, month]);

  return (
    <>
      <div className="page-header">
        <div>
          <h1>Hola, {user?.name.split(" ")[0] ?? "bienvenido"}</h1>
          <p className="muted">Así está su sitio este mes.</p>
        </div>
      </div>

      {error && (
        <p className="error" role="alert">
          ✕ No se pudo cargar su información: {error}
        </p>
      )}
      {!dashboard && !error && <p>Cargando su información…</p>}

      {dashboard && (
        <>
          <section className="cards" aria-label="Estado de su sitio">
            <div className="card kpi">
              <span className="kpi-label">Estado actual</span>
              <strong className="kpi-value">
                <span aria-hidden="true">{ESTADO_ICONO[dashboard.service_status]}</span>{" "}
                {textoEstado(dashboard.service_status)}
              </strong>
              {dashboard.service_name && <span className="muted">{dashboard.service_name}</span>}
            </div>
            <div className="card kpi">
              <span className="kpi-label">Disponibilidad del mes</span>
              <strong className="kpi-value">
                {dashboard.availability === null ? "Sin datos" : formatPercent(dashboard.availability)}
              </strong>
              <span className="muted">
                Objetivo acordado:{" "}
                {dashboard.slo_availability === null ? "sin datos" : formatPercent(dashboard.slo_availability)}
              </span>
            </div>
          </section>

          <section className="card">
            <h2>{textoDisponibilidad(dashboard.availability, dashboard.cumple_objetivo)}</h2>
          </section>

          <section className="card">
            <div className="card-header">
              <h3>Fallas del mes</h3>
              <span className="muted">{incidents.length}</span>
            </div>
            {incidents.length === 0 ? (
              <p>{textosCliente.sinIncidentes}</p>
            ) : (
              <ul className="portal-list">
                {incidents.map((incident) => (
                  <li key={incident.id}>
                    <strong>{incident.title}</strong>
                    <div className="muted">
                      {formatDateTime(incident.started_at)} · {estadosIncidente[incident.status]}
                    </div>
                    {/* Solo el mensaje que la agencia aprobó; los borradores nunca llegan aquí (spec 012) */}
                    {incident.message && <p className="portal-message">{incident.message}</p>}
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section className="card">
            <div className="card-header">
              <h3>Solicitudes del mes</h3>
              <Link to="/portal/solicitudes">Ver todas →</Link>
            </div>
            {tickets.length === 0 ? (
              <p>{textosCliente.sinSolicitudes}</p>
            ) : (
              <ul className="portal-list">
                {tickets.map((ticket) => (
                  <li key={ticket.id}>
                    <strong>{ticket.title}</strong>
                    <div className="muted">
                      {formatDateTime(ticket.created_at)} · {estadosSolicitud[ticket.status]}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}
    </>
  );
}
