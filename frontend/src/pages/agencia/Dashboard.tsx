// Panel de la agencia (spec 010, T14): KPI del mes por cliente, tarjetas de resumen y carga por técnico.
// El estado se comunica con texto e ícono, nunca con color (plan 010).
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { getAgencyDashboard, type AgencyDashboard } from "../../api";
import StatusBadge from "../../components/StatusBadge";
import { formatPercent, formatPrice } from "../../format";

function mesActual(): string {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "America/Bogota",
    year: "numeric",
    month: "2-digit",
  })
    .format(new Date())
    .slice(0, 7);
}

// Valor con «sin datos» cuando la API no tiene serie (CA-8), nunca un 100 % inventado
function textoDisponibilidad(value: number | null): string {
  return value === null ? "Sin datos" : formatPercent(value);
}

function textoObjetivo(cumple: boolean | null): string {
  if (cumple === null) return "Sin datos";
  return cumple ? "✓ Dentro del objetivo" : "! Por debajo del objetivo";
}

export default function AgencyDashboardPage() {
  const [month, setMonth] = useState(mesActual());
  const [data, setData] = useState<AgencyDashboard | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setData(null);
    setError(null);
    getAgencyDashboard(month)
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((e: Error) => {
        if (!cancelled) setError(e.message);
      });
    return () => {
      cancelled = true;
    };
  }, [month]);

  const clients = data?.clients ?? [];
  const conDisponibilidad = clients.filter((client) => client.availability !== null);
  const disponibilidadPromedio =
    conDisponibilidad.length === 0
      ? null
      : conDisponibilidad.reduce((total, client) => total + (client.availability ?? 0), 0) /
        conDisponibilidad.length;
  const abiertas = clients.reduce((total, client) => total + client.open_tickets, 0);
  const horas = clients.reduce((total, client) => total + client.hours, 0);
  const costo = clients.reduce((total, client) => total + client.cost, 0);

  return (
    <>
      <div className="page-header">
        <div>
          <h1>Tablero del mes</h1>
          <p className="muted">Disponibilidad, solicitudes, horas y costo de cada cliente.</p>
        </div>
        <label className="month-picker">
          Mes
          <input type="month" value={month} onChange={(event) => setMonth(event.target.value || mesActual())} />
        </label>
      </div>

      {error && (
        <p className="error" role="alert">
          ✕ No se pudo cargar el tablero: {error}
        </p>
      )}
      {!data && !error && <p>Cargando tablero…</p>}

      {data && (
        <>
          <section className="cards" aria-label="Resumen del mes">
            <div className="card kpi">
              <span className="kpi-label">Clientes</span>
              <strong className="kpi-value">{clients.length}</strong>
            </div>
            <div className="card kpi">
              <span className="kpi-label">Disponibilidad promedio</span>
              <strong className="kpi-value">
                {disponibilidadPromedio === null ? "Sin datos" : formatPercent(disponibilidadPromedio)}
              </strong>
            </div>
            <div className="card kpi">
              <span className="kpi-label">Solicitudes abiertas</span>
              <strong className="kpi-value">{abiertas}</strong>
            </div>
            <div className="card kpi">
              <span className="kpi-label">Horas registradas</span>
              <strong className="kpi-value">{horas.toLocaleString("es-CO")} h</strong>
            </div>
            <div className="card kpi">
              <span className="kpi-label">Costo del mes</span>
              <strong className="kpi-value">{formatPrice(costo)}</strong>
            </div>
          </section>

          <section className="card">
            <div className="card-header">
              <h3>KPI por cliente</h3>
              <span className="muted">{data.month}</span>
            </div>
            {clients.length === 0 ? (
              <p>Todavía no hay clientes registrados.</p>
            ) : (
              <div className="table-scroll">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Cliente</th>
                      <th>Estado</th>
                      <th>Disponibilidad</th>
                      <th>Objetivo</th>
                      <th>SLA</th>
                      <th>MTTR</th>
                      <th>Solicitudes</th>
                      <th>Horas</th>
                      <th>Costo</th>
                      <th />
                    </tr>
                  </thead>
                  <tbody>
                    {clients.map((client) => (
                      <tr key={client.client_id}>
                        <td>
                          <strong>{client.client_name}</strong>
                          <div className="muted">{client.service_name ?? "Sin servicio"}</div>
                        </td>
                        <td>
                          <StatusBadge status={client.service_status} />
                        </td>
                        <td>{textoDisponibilidad(client.availability)}</td>
                        <td>{textoObjetivo(client.cumple_objetivo)}</td>
                        <td>
                          {client.sla_compliance === null ? "Sin datos" : formatPercent(client.sla_compliance)}
                        </td>
                        <td>{client.mttr === null ? "Sin incidentes" : `${client.mttr} min`}</td>
                        <td>
                          {client.open_tickets} abiertas · {client.closed_tickets} cerradas
                        </td>
                        <td>{client.hours.toLocaleString("es-CO")} h</td>
                        <td>{formatPrice(client.cost)}</td>
                        <td>
                          <Link to={`/agencia/clientes/${client.client_id}/metricas`}>Métricas →</Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section className="card">
            <div className="card-header">
              <h3>Carga por técnico</h3>
              <span className="muted">Horas del mes ÷ 120 disponibles</span>
            </div>
            {data.technicians.length === 0 ? (
              <p>No hay técnicos registrados.</p>
            ) : (
              <ul className="load-list">
                {data.technicians.map((technician) => (
                  <li key={technician.user_id}>
                    <div className="load-head">
                      <strong>{technician.name}</strong>
                      <span>
                        {technician.hours.toLocaleString("es-CO")} h · {formatPercent(technician.load * 100)}
                      </span>
                    </div>
                    <div
                      className="load-bar"
                      role="img"
                      aria-label={`Carga de ${technician.name}: ${formatPercent(technician.load * 100)}`}
                    >
                      <span style={{ width: `${Math.min(technician.load * 100, 100)}%` }} />
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
