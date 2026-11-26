// Reportes mensuales de la agencia (spec 013): generar el reporte operativo (toda la agencia) o el ejecutivo de un cliente para un mes,
// y descargar el PDF. Los datos del mes quedan congelados al generarlo: descargar de nuevo da el mismo documento.
import { FormEvent, useCallback, useEffect, useState } from "react";

import { downloadReportPdf, generateReport, listClients, listReports, type ClientSummary, type ReportKind, type ReportSummary } from "../../api";
import { formatDateTime } from "../../format";
import { Select } from "../../components/Select";
import { MonthField } from "../../components/DateFields";

const KIND_LABELS: Record<ReportKind, string> = { operativo: "Operativo (toda la agencia)", ejecutivo: "Ejecutivo (un cliente)" };

// Mes actual en formato AAAA-MM, el que entiende <MonthField >
// En America/Bogota, no en la zona del navegador: cerca del cambio de mes el navegador de otra zona dejaba escoger un mes que en Colombia aún no empieza (auditoría FE-15)
const BOGOTA_MONTH = new Intl.DateTimeFormat("en-CA", { timeZone: "America/Bogota", year: "numeric", month: "2-digit" });
function currentMonth(): string {
  return BOGOTA_MONTH.format(new Date()).slice(0, 7);
}

export default function Reports() {
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [clients, setClients] = useState<ClientSummary[]>([]);
  const [kind, setKind] = useState<ReportKind>("operativo");
  const [clientId, setClientId] = useState<number | null>(null);
  const [month, setMonth] = useState(currentMonth());
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    listReports()
      .then(setReports)
      .catch((e: Error) => setError(e.message));
  }, []);

  useEffect(() => {
    load();
    listClients()
      .then(setClients)
      .catch(() => setClients([]));
  }, [load]);

  async function run(action: () => Promise<unknown>) {
    setBusy(true);
    setError(null);
    try {
      await action();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    void run(async () => {
      const report = await generateReport({ kind, client_id: kind === "ejecutivo" ? clientId : null, month });
      load();
      await downloadReportPdf(report.id);
    });
  }

  return (
    <>
      <h1>Reportes</h1>
      <p className="muted">
        El operativo es para la agencia (KPI, comparación con el mes anterior, carga). El ejecutivo es para el cliente: una página, sin jerga.
      </p>
      <section className="card" aria-label="Generar un reporte">
        <h2>Generar un reporte</h2>
        <form className="stacked-form" onSubmit={handleSubmit}>
          <label>
            Tipo
            <Select value={kind} onChange={(event) => setKind(event.target.value as ReportKind)}>
              {(Object.keys(KIND_LABELS) as ReportKind[]).map((k) => (
                <option key={k} value={k}>
                  {KIND_LABELS[k]}
                </option>
              ))}
            </Select>
          </label>
          {kind === "ejecutivo" && (
            <label>
              Cliente
              <Select value={clientId ?? ""} onChange={(event) => setClientId(event.target.value ? Number(event.target.value) : null)} required>
                <option value="">Elige un cliente</option>
                {clients.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </Select>
            </label>
          )}
          <label>
            Mes
            <MonthField value={month} max={currentMonth()} onChange={(event) => setMonth(event.target.value)} required />
          </label>
          <button type="submit" className="button" disabled={busy || (kind === "ejecutivo" && clientId === null)}>
            {busy ? "Generando…" : "Generar y descargar PDF"}
          </button>
        </form>
        {error && (
          <p role="alert" className="form-error">
            {error}
          </p>
        )}
      </section>

      <section className="card" aria-label="Reportes generados">
        <h2>Reportes generados</h2>
        {reports.length === 0 ? (
          <p className="muted">Todavía no hay reportes generados.</p>
        ) : (
          <table className="table" aria-label="Reportes generados">
            <thead>
              <tr>
                <th>Reporte</th>
                <th>Mes</th>
                <th>Generado</th>
                <th>Por</th>
                <th>PDF</th>
              </tr>
            </thead>
            <tbody>
              {reports.map((report) => (
                <tr key={report.id}>
                  <td>{report.kind === "operativo" ? "Operativo" : `Ejecutivo · ${report.client_name}`}</td>
                  <td>{report.month_label}</td>
                  <td>{formatDateTime(report.created_at)}</td>
                  <td>{report.generated_by ?? "—"}</td>
                  <td>
                    <button type="button" className="button button-secondary" disabled={busy} onClick={() => run(() => downloadReportPdf(report.id))}>
                      Descargar
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </>
  );
}
