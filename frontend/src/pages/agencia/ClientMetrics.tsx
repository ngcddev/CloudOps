// Detalle técnico de un cliente (spec 010, T15): disponibilidad y latencia del mes, en SVG propio,
// con el objetivo del plan y un enlace a Grafana. Con Prometheus apagado se muestra «sin datos» (CA-8).
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
  getClientDashboard,
  getClientSeries,
  type ClientDashboardKpi,
  type ClientSeries,
} from "../../api";
import LineChart from "../../components/LineChart";
import StatusBadge from "../../components/StatusBadge";
import { formatPercent } from "../../format";

// Grafana del clúster de la demo (spec 008); se abre en otra pestaña
const GRAFANA_URL = "http://grafana.hub.local";

function mesActual(): string {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "America/Bogota",
    year: "numeric",
    month: "2-digit",
  })
    .format(new Date())
    .slice(0, 7);
}

// p95 de una serie de latencias (cada punto ya es el p95 de 5 min)
function p95(valores: number[]): number | null {
  if (valores.length === 0) return null;
  const ordenados = [...valores].sort((a, b) => a - b);
  return ordenados[Math.min(ordenados.length - 1, Math.ceil(ordenados.length * 0.95) - 1)];
}

export default function ClientMetrics() {
  const { id } = useParams();
  const clientId = Number(id);
  const [month, setMonth] = useState(mesActual());
  const [series, setSeries] = useState<ClientSeries | null>(null);
  const [client, setClient] = useState<ClientDashboardKpi | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setSeries(null);
    setClient(null);
    setError(null);
    Promise.all([getClientSeries(clientId, month), getClientDashboard(clientId, month)])
      .then(([seriesData, clientData]) => {
        if (cancelled) return;
        setSeries(seriesData);
        setClient(clientData);
      })
      .catch((e: Error) => {
        if (!cancelled) setError(e.message);
      });
    return () => {
      cancelled = true;
    };
  }, [clientId, month]);

  const latencias = series?.latency_p95.map((point) => point.value) ?? [];
  const p95Mes = p95(latencias);
  const ultimaLatencia = latencias.length > 0 ? latencias[latencias.length - 1] : null;

  return (
    <>
      <div className="page-header">
        <div>
          <p className="muted">
            <Link to="/agencia">← Volver al tablero</Link>
          </p>
          <h1>Métricas de {client?.client_name ?? `cliente ${id}`}</h1>
          {client && (
            <p className="muted">
              {client.service_name ?? "Sin servicio"} · <StatusBadge status={client.service_status} />
            </p>
          )}
        </div>
        <div className="page-actions">
          <label className="month-picker">
            Mes
            <input type="month" value={month} onChange={(event) => setMonth(event.target.value || mesActual())} />
          </label>
          <a className="button button-secondary" href={GRAFANA_URL} target="_blank" rel="noreferrer">
            Abrir Grafana ↗
          </a>
        </div>
      </div>

      {error && (
        <p className="error" role="alert">
          ✕ No se pudieron cargar las métricas: {error}
        </p>
      )}
      {!series && !error && <p>Cargando métricas…</p>}

      {series && (
        <>
          <section className="cards" aria-label="Resumen técnico del mes">
            <div className="card kpi">
              <span className="kpi-label">Disponibilidad del mes</span>
              <strong className="kpi-value">
                {client?.availability === null || client?.availability === undefined
                  ? "Sin datos"
                  : formatPercent(client.availability)}
              </strong>
            </div>
            <div className="card kpi">
              <span className="kpi-label">Objetivo del plan</span>
              <strong className="kpi-value">
                {series.slo_availability === null ? "Sin datos" : formatPercent(series.slo_availability)}
              </strong>
            </div>
            <div className="card kpi">
              <span className="kpi-label">p95 del último tramo</span>
              <strong className="kpi-value">
                {ultimaLatencia === null ? "Sin datos" : `${ultimaLatencia.toFixed(2)} s`}
              </strong>
            </div>
            <div className="card kpi">
              <span className="kpi-label">p95 del mes</span>
              <strong className="kpi-value">{p95Mes === null ? "Sin datos" : `${p95Mes.toFixed(2)} s`}</strong>
            </div>
          </section>

          <LineChart
            title="Disponibilidad del sitio"
            points={series.availability}
            kind="percent"
            target={series.slo_availability}
          />
          <LineChart title="Latencia p95" points={series.latency_p95} kind="seconds" />

          <p className="muted">
            Cada punto es un intervalo de 5 minutos. Para el detalle completo del sitio,{" "}
            <a href={GRAFANA_URL} target="_blank" rel="noreferrer">
              abra Grafana ↗
            </a>
            .
          </p>
        </>
      )}
    </>
  );
}
