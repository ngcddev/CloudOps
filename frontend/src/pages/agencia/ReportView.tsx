// Vista de un reporte generado, lista para imprimir o guardar como PDF desde el navegador (spec 013).
// La misma pantalla sirve a la agencia y al portal del cliente; la API decide qué puede ver cada uno.
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { getReport, type Report } from "../../api";
import ExecutiveReport from "../../components/ExecutiveReport";
import OperationalReport from "../../components/OperationalReport";

export default function ReportView({ backTo = "/agencia/reportes" }: { backTo?: string }) {
  const { id } = useParams();
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getReport(Number(id))
      .then(setReport)
      .catch((err: Error) => setError(err.message));
  }, [id]);

  if (error) {
    return (
      <>
        <p className="error" role="alert">
          ✕ No se pudo cargar el reporte: {error}
        </p>
        <Link to={backTo}>Volver a reportes</Link>
      </>
    );
  }
  if (!report) return <p>Cargando reporte…</p>;

  return (
    <>
      <div className="report-toolbar no-print">
        <Link to={backTo}>← Reportes</Link>
        {/* El PDF lo hace el navegador: «Imprimir» → «Guardar como PDF» (decisión 1 de la 013) */}
        <button type="button" className="button" onClick={() => window.print()}>
          Descargar PDF
        </button>
      </div>
      {report.data.kind === "operativo" ? <OperationalReport data={report.data} /> : <ExecutiveReport data={report.data} />}
    </>
  );
}
