// Gráfica de líneas en SVG hecha a mano (spec 010, T15): sin librerías, blanco y negro.
// Si hay un hueco entre dos puntos (> 7,5 min) la línea se corta y se marca «sin datos».
import type { SeriesPoint } from "../api";

interface LineChartProps {
  title: string;
  points: SeriesPoint[];
  // percent: 0–100 con objetivo; seconds: latencia en segundos
  kind: "percent" | "seconds";
  target?: number | null;
}

const WIDTH = 820;
const HEIGHT = 260;
const MARGIN = { top: 18, right: 18, bottom: 34, left: 56 };
// Un punto cada 5 min; dos seguidos separados por más de 7,5 min son un hueco de datos
const GAP_MS = 7.5 * 60 * 1000;

function horaBogota(iso: string): string {
  return new Date(iso).toLocaleTimeString("es-CO", {
    timeZone: "America/Bogota",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function LineChart({ title, points, kind, target }: LineChartProps) {
  const ordered = [...points].sort((a, b) => Date.parse(a.timestamp) - Date.parse(b.timestamp));

  if (ordered.length < 2) {
    return (
      <section className="card">
        <div className="card-header">
          <h3>{title}</h3>
        </div>
        <p className="muted">Sin datos para este mes.</p>
      </section>
    );
  }

  const times = ordered.map((point) => Date.parse(point.timestamp));
  const values = ordered.map((point) => point.value);
  const start = Math.min(...times);
  const end = Math.max(...times);
  const span = Math.max(end - start, 1);

  const yMin =
    kind === "percent"
      ? Math.max(0, Math.floor(Math.min(...values, target ?? 100) - 2))
      : 0;
  const yMax =
    kind === "percent"
      ? 100
      : Math.max(1, Math.ceil(Math.max(...values, target ?? 0) * 1.15 * 10) / 10);

  const innerWidth = WIDTH - MARGIN.left - MARGIN.right;
  const innerHeight = HEIGHT - MARGIN.top - MARGIN.bottom;

  const x = (time: number) => MARGIN.left + ((time - start) / span) * innerWidth;
  const y = (value: number) =>
    MARGIN.top + innerHeight - ((Math.min(Math.max(value, yMin), yMax) - yMin) / (yMax - yMin)) * innerHeight;

  // Segmentos separados por los huecos de datos (CA-6: se ve el corte de la caída)
  const segments: SeriesPoint[][] = [];
  const gaps: { from: number; to: number }[] = [];
  let actual: SeriesPoint[] = [ordered[0]];
  for (let i = 1; i < ordered.length; i += 1) {
    const anterior = Date.parse(ordered[i - 1].timestamp);
    const siguiente = Date.parse(ordered[i].timestamp);
    if (siguiente - anterior > GAP_MS) {
      gaps.push({ from: anterior, to: siguiente });
      segments.push(actual);
      actual = [];
    }
    actual.push(ordered[i]);
  }
  segments.push(actual);

  const unidad = kind === "percent" ? "%" : " s";
  const formatear = (value: number) =>
    kind === "percent" ? `${value.toFixed(1)} %` : `${value.toFixed(2)} s`;

  return (
    <section className="card">
      <div className="card-header">
        <h3>{title}</h3>
        <span className="muted">{formatear(values[values.length - 1])} al final del periodo</span>
      </div>
      <svg
        className="chart"
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        role="img"
        aria-label={`${title}: ${ordered.length} puntos, último valor ${formatear(values[values.length - 1])}`}
      >
        {/* Marco y guías horizontales */}
        {[0, 0.5, 1].map((parte) => {
          const valor = yMin + (yMax - yMin) * (1 - parte);
          return (
            <g key={parte}>
              <line
                x1={MARGIN.left}
                x2={WIDTH - MARGIN.right}
                y1={MARGIN.top + innerHeight * parte}
                y2={MARGIN.top + innerHeight * parte}
                stroke="#bbb"
                strokeWidth="1"
              />
              <text className="chart-label" x={MARGIN.left - 8} y={MARGIN.top + innerHeight * parte + 4} textAnchor="end">
                {kind === "percent" ? `${valor.toFixed(0)} %` : `${valor.toFixed(2)} s`}
              </text>
            </g>
          );
        })}

        {/* Objetivo del plan (solo disponibilidad) */}
        {kind === "percent" && target !== null && target !== undefined && (
          <line
            className="chart-target"
            x1={MARGIN.left}
            x2={WIDTH - MARGIN.right}
            y1={y(target)}
            y2={y(target)}
          />
        )}

        {/* Huecos de datos: el corte de la caída */}
        {gaps.map((gap) => (
          <rect
            key={gap.from}
            className="chart-gap"
            x={x(gap.from)}
            y={MARGIN.top}
            width={Math.max(x(gap.to) - x(gap.from), 1)}
            height={innerHeight}
            opacity="0.35"
          />
        ))}

        {segments.map((segment, index) =>
          segment.length > 1 ? (
            <polyline
              key={index}
              className="chart-line"
              points={segment.map((point) => `${x(Date.parse(point.timestamp))},${y(point.value)}`).join(" ")}
            />
          ) : (
            <circle
              key={index}
              cx={x(Date.parse(segment[0].timestamp))}
              cy={y(segment[0].value)}
              r="2"
              fill="#000"
            />
          ),
        )}

        {/* Eje de tiempo: inicio, mitad y fin */}
        {[0, 0.5, 1].map((parte) => {
          const instante = new Date(start + span * parte).toISOString();
          return (
            <text
              key={parte}
              className="chart-label"
              x={MARGIN.left + innerWidth * parte}
              y={HEIGHT - 10}
              textAnchor={parte === 0 ? "start" : parte === 1 ? "end" : "middle"}
            >
              {horaBogota(instante)}
            </text>
          );
        })}
        <text className="chart-label" x={MARGIN.left} y={MARGIN.top - 6}>
          {unidad.trim()}
        </text>
      </svg>
      {gaps.length > 0 && (
        <p className="muted">
          ✕ {gaps.length === 1 ? "Hay un corte" : `Hay ${gaps.length} cortes`} de datos: el sitio no respondió
          durante ese periodo.
        </p>
      )}
    </section>
  );
}
