// Cuerpo del reporte operativo: KPI de cada cliente con el mes anterior al lado, total de la agencia y carga
// por técnico (spec 013, CA-1). Se imprime en A4 apaisado, en blanco y negro.
import type { ClientKpi, OperationalReportData, ReportTotals } from "../api";
import { formatPercent, formatPrice } from "../format";

// «Sin datos» cuando el KPI no existe: nunca un 0 o un 100 % inventado (docs/kpi.md)
const SIN_DATOS = "sin datos";

function percent(value: number | null): string {
  return value === null ? SIN_DATOS : formatPercent(value);
}

function minutes(value: number | null): string {
  return value === null ? "sin fallas" : `${value.toLocaleString("es-CO", { maximumFractionDigits: 1 })} min`;
}

function hours(value: number): string {
  return `${value.toLocaleString("es-CO", { maximumFractionDigits: 1 })} h`;
}

type Row = Pick<ClientKpi, "availability" | "sla_compliance" | "mttr" | "open_tickets" | "closed_tickets" | "hours" | "cost">;

// Las columnas del reporte, cada una con su forma de mostrarse
const COLUMNS: { label: string; show: (row: Row | ReportTotals) => string }[] = [
  { label: "Disponibilidad", show: (row) => percent(row.availability) },
  { label: "SLA cumplido", show: (row) => percent(row.sla_compliance) },
  { label: "MTTR", show: (row) => minutes(row.mttr) },
  { label: "Solicitudes abiertas / cerradas", show: (row) => `${row.open_tickets} / ${row.closed_tickets}` },
  { label: "Horas", show: (row) => hours(row.hours) },
  { label: "Costo", show: (row) => formatPrice(row.cost) },
];

function Cells({ current, previous }: { current: Row | ReportTotals; previous: Row | ReportTotals }) {
  return (
    <>
      {COLUMNS.map((column) => (
        <td key={column.label}>
          <strong>{column.show(current)}</strong>
          <div className="muted">{column.show(previous)}</div>
        </td>
      ))}
    </>
  );
}

export default function OperationalReport({ data }: { data: OperationalReportData }) {
  return (
    <article className="report report-operational">
      <header className="report-header">
        <h1>Reporte operativo · {data.month}</h1>
        <p className="muted">
          Forja Digital · cada celda muestra el mes {data.month} en negrita y debajo el mes anterior ({data.previous_month}).
          Costo con {formatPrice(data.hourly_cost)} por hora de soporte.
        </p>
      </header>

      <table className="table report-table">
        <thead>
          <tr>
            <th>Cliente</th>
            {COLUMNS.map((column) => (
              <th key={column.label}>{column.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.clients.map((row) => (
            <tr key={row.client_id}>
              <td>
                <strong>{row.client_name}</strong>
                <div className="muted">{row.service_name ?? "Sin servicio"}</div>
              </td>
              <Cells current={row.current} previous={row.previous} />
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr>
            <td>
              <strong>Total de la agencia</strong>
              <div className="muted">Promedios de los clientes con dato</div>
            </td>
            <Cells current={data.totals.current} previous={data.totals.previous} />
          </tr>
        </tfoot>
      </table>

      <section className="report-section">
        <h2>Carga por técnico</h2>
        <table className="table report-table">
          <thead>
            <tr>
              <th>Técnico</th>
              <th>Horas del mes</th>
              <th>Carga</th>
            </tr>
          </thead>
          <tbody>
            {data.technicians.map((technician) => (
              <tr key={technician.user_id}>
                <td>{technician.name}</td>
                <td>{hours(technician.hours)}</td>
                <td>{formatPercent(Math.round(technician.load * 1000) / 10)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </article>
  );
}
