// Reportes del portal del cliente: los reportes mensuales de su empresa, para ver y descargar (spec 013, T11).
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { listReports, type ReportSummary } from "../../api";
import { useAuth } from "../../auth";
import { formatDateTime } from "../../format";

const MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];

// 2026-10 → «Octubre de 2026»
function monthName(month: string): string {
  const [year, number] = month.split("-").map(Number);
  const name = MESES[number - 1];
  return `${name.charAt(0).toUpperCase()}${name.slice(1)} de ${year}`;
}

export default function PortalReportList() {
  const { user } = useAuth();
  const clientId = user?.client_id ?? undefined;
  const [reports, setReports] = useState<ReportSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // La API ya limita al cliente a sus reportes ejecutivos; el filtro es para los datos de prueba
    listReports({ kind: "ejecutivo", client_id: clientId })
      .then(setReports)
      .catch((err: Error) => setError(err.message));
  }, [clientId]);

  return (
    <>
      <div className="page-header">
        <h1>Reportes</h1>
      </div>
      <p className="muted">Cada mes le contamos en una página cómo estuvo su sitio. Puede descargarlos en PDF.</p>

      {error && (
        <p className="error" role="alert">
          ✕ {error}
        </p>
      )}
      {!reports && !error && <p>Cargando reportes…</p>}
      {reports && reports.length === 0 && <p>Todavía no hay reportes de su sitio.</p>}
      {reports && reports.length > 0 && (
        <ul className="portal-list">
          {reports.map((report) => (
            <li key={report.id}>
              <Link to={`/portal/reportes/${report.id}`}>
                <strong>{monthName(report.month)}</strong>
              </Link>
              <div className="muted">Preparado el {formatDateTime(report.created_at)}</div>
            </li>
          ))}
        </ul>
      )}
    </>
  );
}
