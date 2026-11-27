// Reportes del cliente en su portal (spec 013): su reporte ejecutivo de cada mes, de una página y en lenguaje simple, para descargar en PDF.
import { useEffect, useState } from "react";

import { downloadReportPdf, listReports, type ReportSummary } from "../../api";

export default function PortalReports() {
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    listReports()
      .then(setReports)
      .catch((e: Error) => setError(e.message));
  }, []);

  async function download(id: number) {
    setBusy(true);
    setError(null);
    try {
      await downloadReportPdf(id);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <h1>Sus reportes</h1>
      <p className="muted">Cada mes le resumimos cómo estuvo su sitio, las fallas que hubo y las solicitudes que atendimos.</p>
      {error && (
        <p role="alert" className="form-error">
          {error}
        </p>
      )}
      <section className="card" aria-label="Reportes">
        {reports.length === 0 ? (
          <p>Todavía no hay reportes disponibles. Aparecerán aquí cuando la agencia los genere.</p>
        ) : (
          <ul className="portal-list">
            {reports.map((report) => (
              <li key={report.id}>
                <strong>Reporte de {report.month_label}</strong>
                <div>
                  <button type="button" className="button button-secondary" disabled={busy} onClick={() => download(report.id)}>
                    Descargar PDF
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </>
  );
}
