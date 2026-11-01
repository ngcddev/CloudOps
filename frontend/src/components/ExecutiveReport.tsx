// Cuerpo del reporte ejecutivo de un cliente: una página A4, sin jerga (spec 013, CA-2 y CA-3).
// Todo el texto viene de la API ya escrito con el glosario; aquí solo se acomoda.
import type { ExecutiveReportData } from "../api";
import { formatPercent } from "../format";

export default function ExecutiveReport({ data }: { data: ExecutiveReportData }) {
  const { availability, incidents, changes, tickets } = data;
  return (
    <article className="report report-executive">
      <header className="report-header">
        <p className="muted">Forja Digital · Reporte del servicio</p>
        <h1>{data.client_name}</h1>
        <p>
          {data.service_name ?? "Sitio web"}
          {data.plan_name && ` · Plan ${data.plan_name}`} · {data.month_label}
        </p>
      </header>

      <section className="report-section">
        <h2>Disponibilidad</h2>
        <div className="report-figures">
          <div>
            <span className="muted">Este mes</span>
            <strong>{availability.value === null ? "Sin datos" : formatPercent(availability.value)}</strong>
          </div>
          <div>
            <span className="muted">Objetivo acordado</span>
            <strong>{availability.objective === null ? "—" : formatPercent(availability.objective)}</strong>
          </div>
        </div>
        <p>
          <span aria-hidden="true">
            {availability.meets_objective === null ? "○" : availability.meets_objective ? "✓" : "!"}
          </span>{" "}
          {availability.text}
        </p>
      </section>

      <section className="report-section">
        <h2>Fallas y recuperación</h2>
        <p>{incidents.text}</p>
        {incidents.items.length > 0 && (
          <ul className="report-list">
            {incidents.items.map((item, index) => (
              <li key={index}>
                <span className="muted">
                  {item.date} · {item.time}
                </span>
                <div>{item.text}</div>
              </li>
            ))}
          </ul>
        )}
        {incidents.recovery_text && <p>{incidents.recovery_text}</p>}
      </section>

      <section className="report-section">
        <h2>Actualizaciones de su sitio</h2>
        <p>{changes.text}</p>
        {changes.items.length > 0 && (
          <ul className="report-list">
            {changes.items.map((item, index) => (
              <li key={index}>
                <span className="muted">{item.date}</span> · {item.text}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="report-section">
        <h2>Solicitudes</h2>
        <p>{tickets.text}</p>
      </section>
    </article>
  );
}
