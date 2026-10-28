// Detalle de un incidente: relojes del SLA, línea de tiempo, enlaces para diagnosticar y acciones del técnico (spec 008).
import { FormEvent, useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
  acknowledgeIncident,
  addIncidentNote,
  closeIncident,
  getIncident,
  mitigateIncident,
  responseStoppedAt,
  type IncidentDetail as IncidentDetailData,
  type IncidentEventType,
} from "../../api";
import RecoveryPanel from "../../components/RecoveryPanel";
import SlaClock from "../../components/SlaClock";
import { formatDateTime } from "../../format";
import { INCIDENT_SOURCE_LABELS, INCIDENT_STATUS_LABELS } from "./IncidentList";

// Cada cuánto se vuelve a pedir el detalle: la recuperación que ve el monitoreo aparece sola
const REFRESH_MS = 10_000;
// Mientras un rollback no esté recuperado se lee más seguido para mostrar su avance (spec 009)
const ROLLBACK_REFRESH_MS = 5_000;

const EVENT_LABELS: Record<IncidentEventType, { icon: string; text: string }> = {
  detectado: { icon: "✗", text: "Detectado" },
  tomado: { icon: "→", text: "Tomado" },
  nota: { icon: "·", text: "Nota" },
  recuperado: { icon: "✓", text: "Recuperado" },
  cerrado: { icon: "■", text: "Cerrado" },
  rollback_enviado: { icon: "↺", text: "Rollback enviado" },
  rollback_confirmado: { icon: "✓", text: "Rollback confirmado" },
  mensaje_cliente: { icon: "✉", text: "Mensaje al cliente" },
};

export default function IncidentDetail() {
  const { id } = useParams();
  const incidentId = Number(id);
  const [incident, setIncident] = useState<IncidentDetailData | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState("");
  const [rootCause, setRootCause] = useState("");

  const load = useCallback(() => {
    getIncident(incidentId)
      .then((data) => {
        setIncident(data);
        setLoadError(null);
      })
      .catch((error: Error) => setLoadError(error.message));
  }, [incidentId]);

  const rollbackStatus = incident?.rollback.status;
  const rollbackRunning = rollbackStatus === "enviado" || rollbackStatus === "sincronizando";
  useEffect(() => {
    load();
    const timer = window.setInterval(load, rollbackRunning ? ROLLBACK_REFRESH_MS : REFRESH_MS);
    return () => window.clearInterval(timer);
  }, [load, rollbackRunning]);

  // Corre una acción y pinta el detalle que devuelve la API, sin recargar la página
  async function run(action: () => Promise<IncidentDetailData>, after?: () => void) {
    setBusy(true);
    setActionError(null);
    try {
      setIncident(await action());
      after?.();
    } catch (error) {
      setActionError((error as Error).message);
    } finally {
      setBusy(false);
    }
  }

  function handleNote(event: FormEvent) {
    event.preventDefault();
    run(() => addIncidentNote(incidentId, note), () => setNote(""));
  }

  function handleClose(event: FormEvent) {
    event.preventDefault();
    run(() => closeIncident(incidentId, rootCause), () => setRootCause(""));
  }

  if (loadError && !incident) {
    return (
      <>
        <p className="error" role="alert">
          ✕ No se pudo cargar el incidente: {loadError}
        </p>
        <Link to="/agencia/incidentes">Volver a incidentes</Link>
      </>
    );
  }
  if (!incident) return <p>Cargando incidente…</p>;

  const open = incident.status === "abierto";
  const closed = incident.status === "cerrado";
  const last = incident.last_change;

  return (
    <>
      <p>
        <Link to="/agencia/incidentes">← Incidentes</Link>
      </p>
      <div className="page-header">
        <div>
          <h1>{incident.title}</h1>
          <div className="muted">
            #{incident.id} · {incident.client_name} · {incident.service_name} · {INCIDENT_SOURCE_LABELS[incident.source]}
          </div>
        </div>
        <div className="ticket-meta">
          <span className={`priority-badge priority-${incident.priority}`}>{incident.priority}</span>
          <span className={`status-pill status-${incident.status}`}>{INCIDENT_STATUS_LABELS[incident.status]}</span>
        </div>
      </div>

      {actionError && (
        <p className="error" role="alert">
          ✕ {actionError}
        </p>
      )}

      <section className="card" aria-label="Reloj del SLA">
        <h2>Reloj del SLA</h2>
        <div className="detail-grid">
          <SlaClock
            label="Respuesta (al tomarlo o mitigarlo)"
            start={incident.started_at}
            due={incident.response_due_at}
            done={responseStoppedAt(incident)}
          />
          <SlaClock
            label="Solución (al mitigarlo)"
            start={incident.started_at}
            due={incident.resolution_due_at}
            done={incident.mitigated_at}
          />
        </div>
        <dl className="data">
          <dt>Inicio de la falla</dt>
          <dd>{formatDateTime(incident.started_at)}</dd>
          <dt>Responsable</dt>
          <dd>{incident.assignee_name ?? "Sin tomar"}</dd>
          <dt>Mitigado</dt>
          <dd>{formatDateTime(incident.mitigated_at)}</dd>
          <dt>Cerrado</dt>
          <dd>{formatDateTime(incident.closed_at)}</dd>
          {incident.root_cause && (
            <>
              <dt>Causa raíz</dt>
              <dd>{incident.root_cause}</dd>
            </>
          )}
        </dl>
      </section>

      {(!closed || incident.rollback.status !== "sin_rollback") && (
        <RecoveryPanel incident={incident} onUpdated={setIncident} />
      )}

      <div className="detail-grid">
        <section className="card" aria-label="Diagnóstico">
          <h2>Diagnóstico</h2>
          <ul className="history-list">
            <li>
              <strong>Registros del sitio</strong>
              <div>
                {incident.logs_url ? (
                  <a href={incident.logs_url} target="_blank" rel="noreferrer">
                    Abrir en Grafana ↗
                  </a>
                ) : (
                  <span className="muted">Sin Grafana configurado</span>
                )}
              </div>
            </li>
            <li>
              <strong>Último cambio del servicio</strong>
              {last ? (
                <div>
                  {last.version} · {last.source === "rollback" ? "recuperación" : "cambio"} de {last.author} ·{" "}
                  {formatDateTime(last.deployed_at)}
                  <div>
                    {last.commit_url ? (
                      <a href={last.commit_url} target="_blank" rel="noreferrer">
                        Ver commit {last.commit_sha?.slice(0, 8)} en Gitea ↗
                      </a>
                    ) : (
                      <span className="muted">Sin enlace al commit</span>
                    )}
                  </div>
                </div>
              ) : (
                <div className="muted">El servicio no tiene publicaciones registradas.</div>
              )}
            </li>
          </ul>
        </section>

        <section className="card" aria-label="Acciones">
          <h2>Acciones</h2>
          {closed && <p className="muted">El incidente está cerrado.</p>}
          {!closed && (
            <div className="stacked-form">
              {!incident.acknowledged_at && (
                <button type="button" className="button" disabled={busy} onClick={() => run(() => acknowledgeIncident(incidentId))}>
                  Tomar incidente
                </button>
              )}
              {open && (incident.source === "manual" || incident.rollback.confirmed_at !== null) && (
                <button type="button" className="button" disabled={busy} onClick={() => run(() => mitigateIncident(incidentId))}>
                  Marcar como mitigado
                </button>
              )}
              {open && incident.source === "alerta" && incident.rollback.confirmed_at === null && (
                <p className="muted">Se marca mitigado solo cuando el monitoreo ve el sitio responder.</p>
              )}
            </div>
          )}
          {!closed && (
            <form className="stacked-form" onSubmit={handleNote}>
              <label>
                Nota para la línea de tiempo
                <textarea value={note} onChange={(event) => setNote(event.target.value)} rows={2} maxLength={2000} />
              </label>
              <button type="submit" className="button button-secondary" disabled={busy || !note.trim()}>
                Agregar nota
              </button>
            </form>
          )}
          {incident.status === "mitigado" && (
            <form className="stacked-form" onSubmit={handleClose}>
              <label>
                Causa raíz
                <textarea value={rootCause} onChange={(event) => setRootCause(event.target.value)} rows={3} maxLength={2000} required />
              </label>
              <button type="submit" className="button" disabled={busy || !rootCause.trim()}>
                Cerrar incidente
              </button>
            </form>
          )}
        </section>
      </div>

      <section className="card" aria-label="Línea de tiempo">
        <h2>Línea de tiempo</h2>
        <ol className="history-list">
          {incident.events.map((event) => {
            const label = EVENT_LABELS[event.type];
            return (
              <li key={event.id}>
                <strong>
                  <span aria-hidden="true">{label.icon}</span> {label.text}
                </strong>{" "}
                · {event.actor_name}
                {event.message && <div>{event.message}</div>}
                <div className="muted">{formatDateTime(event.created_at)}</div>
              </li>
            );
          })}
        </ol>
      </section>
    </>
  );
}
