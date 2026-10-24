import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
  assignTicket,
  classifyTicket,
  createChangeRequest,
  createWorkLog,
  getTicket,
  listChangeRequests,
  transitionTicket,
  type ChangeRequest,
  type Ticket,
  type TicketDetail as TicketDetailData,
  type TicketImpact,
  type TicketPriority,
  type TicketStatus,
  type TicketUrgency,
} from "../../api";

type SlaState = "a_tiempo" | "en_riesgo" | "vencido";

const SLA_LABELS: Record<SlaState, string> = {
  a_tiempo: "a tiempo",
  en_riesgo: "en riesgo",
  vencido: "vencido",
};

const SLA_ICONS: Record<SlaState, string> = {
  a_tiempo: "✓",
  en_riesgo: "⚠",
  vencido: "✕",
};

// Texto de cada estado de un cambio (glosario)
const CHANGE_STATUS_TEXT: Record<ChangeRequest["status"], string> = {
  pendiente: "Pendiente",
  aprobada: "Aprobada",
  en_validacion: "En validación",
  desplegada: "Publicada",
  rechazada: "Rechazada",
  fallida: "No se pudo publicar",
};

function getTicketSlaState(ticket: Ticket): SlaState {
  if (!ticket.created_at) return "a_tiempo";
  const createdAt = new Date(ticket.created_at).getTime();
  const dueAt = ticket.first_response_at
    ? new Date(ticket.resolution_due_at ?? ticket.response_due_at ?? ticket.created_at).getTime()
    : new Date(ticket.response_due_at ?? ticket.resolution_due_at ?? ticket.created_at).getTime();
  if (!Number.isFinite(dueAt) || dueAt <= 0) return "a_tiempo";
  const now = Date.now();
  if (now >= dueAt) return "vencido";
  const totalWindow = dueAt - createdAt;
  const elapsed = now - createdAt;
  if (totalWindow > 0 && elapsed * 5 >= totalWindow * 4) return "en_riesgo";
  return "a_tiempo";
}

export default function TicketDetail() {
  const { id } = useParams();
  const [ticket, setTicket] = useState<TicketDetailData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [classifyForm, setClassifyForm] = useState({ impact: "alto", urgency: "media", priority: "P2", correction_reason: "" });
  const [assignForm, setAssignForm] = useState({ assignee_id: "2" });
  const [transitionForm, setTransitionForm] = useState({ new_status: "en_progreso" as Exclude<TicketStatus, "abierto"> });
  const [workLogForm, setWorkLogForm] = useState({ hours: "1.5", note: "" });
  // Cambios de versión registrados desde esta solicitud (spec 005)
  const [changes, setChanges] = useState<ChangeRequest[]>([]);
  const [targetVersion, setTargetVersion] = useState("");
  const [changeError, setChangeError] = useState<string | null>(null);

  useEffect(() => {
    listChangeRequests({ ticket_id: Number(id) })
      .then(setChanges)
      .catch(() => setChanges([]));
  }, [id]);

  useEffect(() => {
    setTicket(null);
    setError(null);
    getTicket(Number(id))
      .then((data) => {
        setTicket(data);
        setClassifyForm({
          impact: data.impact ?? "alto",
          urgency: data.urgency ?? "media",
          priority: data.priority ?? "P2",
          correction_reason: "",
        });
        setAssignForm({ assignee_id: String(data.assignee_id ?? 2) });
      })
      .catch((loadError: Error) => setError(loadError.message));
  }, [id]);

  const slaState = useMemo(() => (ticket ? getTicketSlaState(ticket) : "a_tiempo"), [ticket]);

  async function handleClassify(event: React.FormEvent) {
    event.preventDefault();
    if (!ticket) return;
    try {
      const updated = await classifyTicket(ticket.id, {
        impact: classifyForm.impact as TicketImpact,
        urgency: classifyForm.urgency as TicketUrgency,
        priority: classifyForm.priority as TicketPriority,
        correction_reason: classifyForm.correction_reason || null,
      });
      setTicket((current) => (current ? { ...current, ...updated } : current));
      setClassifyForm((current) => ({ ...current, correction_reason: "" }));
    } catch (submitError) {
      setError((submitError as Error).message);
    }
  }

  async function handleAssign(event: React.FormEvent) {
    event.preventDefault();
    if (!ticket) return;
    try {
      const updated = await assignTicket(ticket.id, { assignee_id: Number(assignForm.assignee_id) });
      setTicket((current) => (current ? { ...current, ...updated } : current));
    } catch (submitError) {
      setError((submitError as Error).message);
    }
  }

  async function handleTransition(event: React.FormEvent) {
    event.preventDefault();
    if (!ticket) return;
    try {
      const updated = await transitionTicket(ticket.id, { new_status: transitionForm.new_status });
      setTicket((current) => (current ? { ...current, ...updated } : current));
    } catch (submitError) {
      setError((submitError as Error).message);
    }
  }

  async function handleRegisterChange(event: React.FormEvent) {
    event.preventDefault();
    if (!ticket) return;
    setChangeError(null);
    try {
      const created = await createChangeRequest({
        ticket_id: ticket.id,
        to_version: targetVersion,
      });
      setChanges((current) => [created, ...current]);
      setTargetVersion("");
    } catch (submitError) {
      setChangeError((submitError as Error).message);
    }
  }

  async function handleWorkLog(event: React.FormEvent) {
    event.preventDefault();
    if (!ticket) return;
    try {
      const log = await createWorkLog(ticket.id, {
        hours: Number(workLogForm.hours),
        note: workLogForm.note || null,
      });
      setTicket((current) => {
        if (!current) return current;
        return {
          ...current,
          work_logs: [log, ...current.work_logs],
        };
      });
      setWorkLogForm({ hours: "1.5", note: "" });
    } catch (submitError) {
      setError((submitError as Error).message);
    }
  }

  return (
    <>
      <p>
        <Link to="/agencia/tickets">← Volver a la bandeja</Link>
      </p>

      {error && (
        <p className="error" role="alert">
          ✕ No se pudo cargar la solicitud: {error}
        </p>
      )}

      {!ticket && !error && <p>Cargando solicitud…</p>}

      {ticket && (
        <>
          <div className="page-header">
            <div>
              <h1>{ticket.title}</h1>
              <div className="muted">#{ticket.id}</div>
            </div>
            <div className="ticket-meta">
              <span className={`priority-badge priority-${ticket.priority ?? "sin-prioridad"}`}>{ticket.priority ?? "—"}</span>
              <span className={`status-pill status-${ticket.status}`}>{ticket.status}</span>
              <span className={`sla-badge sla-${slaState}`}>
                {SLA_ICONS[slaState]} {SLA_LABELS[slaState]}
              </span>
            </div>
          </div>

          <section className="card">
            <h2>Datos de la solicitud</h2>
            <dl className="data">
              <dt>Cliente / servicio</dt>
              <dd>
                {ticket.service_id} · {ticket.kind}
              </dd>
              <dt>Descripción</dt>
              <dd>{ticket.description}</dd>
              <dt>Impacto</dt>
              <dd>{ticket.impact ?? "—"}</dd>
              <dt>Urgencia</dt>
              <dd>{ticket.urgency ?? "—"}</dd>
              <dt>Responsable</dt>
              <dd>{ticket.assignee_id ?? "Sin asignar"}</dd>
              <dt>Creada</dt>
              <dd>{new Date(ticket.created_at).toLocaleString("es-CO")}</dd>
              <dt>Respuesta</dt>
              <dd>{ticket.response_due_at ? new Date(ticket.response_due_at).toLocaleString("es-CO") : "—"}</dd>
              <dt>Solución</dt>
              <dd>{ticket.resolution_due_at ? new Date(ticket.resolution_due_at).toLocaleString("es-CO") : "—"}</dd>
            </dl>
          </section>

          <div className="detail-grid">
            <section className="card">
              <h3>Clasificar</h3>
              <form onSubmit={handleClassify} className="stacked-form">
                <label>
                  <span>Impacto</span>
                  <select value={classifyForm.impact} onChange={(event) => setClassifyForm((current) => ({ ...current, impact: event.target.value }))}>
                    <option value="alto">Alto</option>
                    <option value="medio">Medio</option>
                    <option value="bajo">Bajo</option>
                  </select>
                </label>
                <label>
                  <span>Urgencia</span>
                  <select value={classifyForm.urgency} onChange={(event) => setClassifyForm((current) => ({ ...current, urgency: event.target.value }))}>
                    <option value="alta">Alta</option>
                    <option value="media">Media</option>
                    <option value="baja">Baja</option>
                  </select>
                </label>
                <label>
                  <span>Prioridad</span>
                  <select value={classifyForm.priority} onChange={(event) => setClassifyForm((current) => ({ ...current, priority: event.target.value as TicketPriority }))}>
                    <option value="P1">P1</option>
                    <option value="P2">P2</option>
                    <option value="P3">P3</option>
                    <option value="P4">P4</option>
                  </select>
                </label>
                <label>
                  <span>Motivo de corrección</span>
                  <textarea
                    rows={3}
                    value={classifyForm.correction_reason}
                    onChange={(event) => setClassifyForm((current) => ({ ...current, correction_reason: event.target.value }))}
                  />
                </label>
                <button type="submit" className="button">Guardar clasificación</button>
              </form>
            </section>

            <section className="card">
              <h3>Asignar responsable</h3>
              <form onSubmit={handleAssign} className="stacked-form">
                <label>
                  <span>Usuario responsable</span>
                  <input type="number" value={assignForm.assignee_id} onChange={(event) => setAssignForm({ assignee_id: event.target.value })} />
                </label>
                <button type="submit" className="button">Asignar</button>
              </form>
            </section>

            <section className="card">
              <h3>Cambiar estado</h3>
              <form onSubmit={handleTransition} className="stacked-form">
                <label>
                  <span>Nuevo estado</span>
                  <select value={transitionForm.new_status} onChange={(event) => setTransitionForm({ new_status: event.target.value as Exclude<TicketStatus, "abierto"> })}>
                    <option value="en_progreso">En progreso</option>
                    <option value="en_espera">En espera</option>
                    <option value="resuelto">Resuelto</option>
                    <option value="cerrado">Cerrado</option>
                  </select>
                </label>
                <button type="submit" className="button">Actualizar estado</button>
              </form>
            </section>

            <section className="card">
              <h3>Registrar horas</h3>
              <form onSubmit={handleWorkLog} className="stacked-form">
                <label>
                  <span>Horas</span>
                  <input type="number" step="0.5" min="0.5" value={workLogForm.hours} onChange={(event) => setWorkLogForm((current) => ({ ...current, hours: event.target.value }))} />
                </label>
                <label>
                  <span>Nota</span>
                  <textarea rows={3} value={workLogForm.note} onChange={(event) => setWorkLogForm((current) => ({ ...current, note: event.target.value }))} />
                </label>
                <button type="submit" className="button">Guardar horas</button>
              </form>
            </section>
          </div>

          {ticket.kind === "cambio" && (
            <section className="card" aria-labelledby="registrar-cambio">
              <h3 id="registrar-cambio">Cambio de versión</h3>
              {changes.length > 0 && (
                <ul className="history-list">
                  {changes.map((change) => (
                    <li key={change.id}>
                      <strong>
                        {change.from_version} → {change.to_version}
                      </strong>
                      <div>
                        <span className={`status-pill change-${change.status}`}>{CHANGE_STATUS_TEXT[change.status]}</span>
                      </div>
                      {change.rejection_reason && <div className="muted">Motivo: {change.rejection_reason}</div>}
                    </li>
                  ))}
                </ul>
              )}
              <form onSubmit={handleRegisterChange} className="stacked-form">
                <label>
                  <span>Versión destino</span>
                  <input
                    type="text"
                    value={targetVersion}
                    placeholder="v1.1"
                    required
                    onChange={(event) => setTargetVersion(event.target.value)}
                  />
                </label>
                {changeError && (
                  <p className="error" role="alert">
                    ✕ {changeError}
                  </p>
                )}
                <button type="submit" className="button">Registrar cambio</button>
              </form>
              <p className="muted">
                El cambio queda pendiente en la <Link to="/agencia/cambios">bandeja de cambios</Link>, donde se aprueba
                o se rechaza.
              </p>
            </section>
          )}

          <section className="card">
            <h3>Historial</h3>
            {ticket.events.length === 0 && <p>No hay historial para esta solicitud.</p>}
            {ticket.events.length > 0 && (
              <ul className="history-list">
                {ticket.events.map((event) => (
                  <li key={event.id}>
                    <strong>{event.type}</strong>
                    <div className="muted">{new Date(event.created_at).toLocaleString("es-CO")}</div>
                    <div>
                      {event.from_value ?? "—"} → {event.to_value ?? "—"}
                    </div>
                    {event.note && <div>{event.note}</div>}
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section className="card">
            <h3>Horas trabajadas</h3>
            {ticket.work_logs.length === 0 && <p>No se registraron horas todavía.</p>}
            {ticket.work_logs.length > 0 && (
              <ul className="history-list">
                {ticket.work_logs.map((log) => (
                  <li key={log.id}>
                    <strong>{log.hours} h</strong>
                    <div className="muted">{new Date(log.created_at).toLocaleString("es-CO")}</div>
                    {log.note && <div>{log.note}</div>}
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}
    </>
  );
}
