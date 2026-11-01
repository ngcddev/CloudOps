// Reportes mensuales de la agencia: generar un operativo o un ejecutivo y ver los ya generados (spec 013).
import { FormEvent, useCallback, useEffect, useState } from "react";

import {
  createReport,
  listClients,
  listReports,
  mesActual,
  type ClientSummary,
  type ReportKind,
  type ReportSummary,
} from "../../api";
import { formatDateTime } from "../../format";

export const REPORT_KIND_LABELS: Record<ReportKind, string> = {
  operativo: "Operativo",
  ejecutivo: "Ejecutivo",
};

export default function ReportList() {
  const [reports, setReports] = useState<ReportSummary[] | null>(null);
  const [clients, setClients] = useState<ClientSummary[]>([]);
  const [kind, setKind] = useState<ReportKind>("operativo");
  const [clientId, setClientId] = useState<number | "">("");
  const [month, setMonth] = useState(mesActual());
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    listReports()
      .then(setReports)
      .catch((err: Error) => setError(err.message));
  }, []);

  useEffect(() => {
    load();
    listClients()
      .then(setClients)
      .catch((err: Error) => setError(err.message));
  }, [load]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await createReport(kind, month, kind === "ejecutivo" && clientId !== "" ? clientId : undefined);
      load();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <div className="page-header">
        <h1>Reportes</h1>
      </div>
      <p className="muted">
        El operativo muestra los KPI de todos los clientes frente al mes anterior; el ejecutivo resume en una página, sin
        jerga, lo que recibió un cliente. Los números quedan fijos al generarlo.
      </p>

      {error && (
        <p className="error" role="alert">
          ✕ {error}
        </p>
      )}

      <section className="card" aria-label="Generar reporte">
        <h2>Generar reporte</h2>
        <form className="stacked-form report-form" onSubmit={handleSubmit}>
          <label>
            Tipo
            <select value={kind} onChange={(event) => setKind(event.target.value as ReportKind)}>
              <option value="operativo">Operativo (agencia)</option>
              <option value="ejecutivo">Ejecutivo (un cliente)</option>
            </select>
          </label>
          {kind === "ejecutivo" && (
            <label>
              Cliente
              <select
                value={clientId}
                required
                onChange={(event) => setClientId(event.target.value ? Number(event.target.value) : "")}
              >
                <option value="">Elige un cliente</option>
                {clients.map((client) => (
                  <option key={client.id} value={client.id}>
                    {client.name}
                  </option>
                ))}
              </select>
            </label>
          )}
          <label>
            Mes
            <input type="month" value={month} required onChange={(event) => setMonth(event.target.value)} />
          </label>
          <button type="submit" className="button" disabled={busy || (kind === "ejecutivo" && clientId === "")}>
            {busy ? "Generando…" : "Generar"}
          </button>
        </form>
      </section>

      {!reports && !error && <p>Cargando reportes…</p>}
      {reports && reports.length === 0 && <p>Todavía no hay reportes generados.</p>}
      {reports && reports.length > 0 && (
        <table className="table">
          <thead>
            <tr>
              <th>Reporte</th>
              <th>Mes</th>
              <th>Generado</th>
            </tr>
          </thead>
          <tbody>
            {reports.map((report) => (
              <tr key={report.id}>
                <td>
                  <strong>{REPORT_KIND_LABELS[report.kind]}</strong>
                  <div className="muted">{report.client_name ?? "Todos los clientes"}</div>
                </td>
                <td>{report.month}</td>
                <td>
                  {formatDateTime(report.created_at)}
                  {report.generated_by_name && <div className="muted">por {report.generated_by_name}</div>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  );
}
