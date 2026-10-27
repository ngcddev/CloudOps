// Bloque «Recuperación» del detalle de un incidente: versión actual → destino, botón Rollback con
// confirmación, avance Enviado → Sincronizando → Recuperado, MTTR y mensaje para el cliente (spec 009).
import { useEffect, useRef, useState } from "react";

import {
  getClientMessage,
  getRollbackPlan,
  rollbackIncident,
  type IncidentDetail,
  type RollbackPlan,
  type RollbackStatus,
} from "../api";
import { formatDateTime } from "../format";

// Los pasos del avance; el estado se dice con texto e ícono, no con color
const STEPS: { status: Exclude<RollbackStatus, "sin_rollback">; label: string }[] = [
  { status: "enviado", label: "Enviado" },
  { status: "sincronizando", label: "Sincronizando" },
  { status: "recuperado", label: "Recuperado" },
];

// El último paso, ya alcanzado, se marca completo: no queda nada por esperar
function stepIcon(index: number, current: number): string {
  if (index < current || (index === current && STEPS[index].status === "recuperado")) return "✓";
  return index === current ? "●" : "○";
}

// 7.5 → "7,5 minutos"; 1 → "1 minuto"
export function formatMttr(minutes: number): string {
  const text = minutes.toLocaleString("es-CO", { maximumFractionDigits: 1 });
  return `${text} ${minutes === 1 ? "minuto" : "minutos"}`;
}

interface Props {
  incident: IncidentDetail;
  // Recibe el detalle que devuelve la API al pedir el rollback, para pintarlo sin recargar
  onUpdated: (incident: IncidentDetail) => void;
}

export default function RecoveryPanel({ incident, onUpdated }: Props) {
  const { rollback } = incident;
  const [plan, setPlan] = useState<RollbackPlan | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState(false);
  const dialog = useRef<HTMLDialogElement>(null);

  // El plan solo se pide mientras todavía se puede pedir el rollback; después las versiones salen del incidente
  const planned = incident.status === "abierto" && rollback.status === "sin_rollback";
  useEffect(() => {
    if (!planned) return;
    getRollbackPlan(incident.id)
      .then(setPlan)
      .catch((err: Error) => setError(err.message));
  }, [incident.id, planned, incident.events.length]);

  // El mensaje para el cliente solo existe cuando el incidente ya se mitigó
  const mitigated = incident.mitigated_at !== null;
  useEffect(() => {
    if (!mitigated) {
      setMessage(null);
      return;
    }
    getClientMessage(incident.id)
      .then((data) => setMessage(data.message))
      .catch((err: Error) => setError(err.message));
  }, [incident.id, mitigated, incident.mitigated_at]);

  const from = rollback.from_version ?? plan?.current_version ?? null;
  const to = rollback.to_version ?? plan?.target_version ?? null;
  const started = rollback.status !== "sin_rollback";
  const canRollback = planned && plan?.can_rollback === true && !busy;
  // Mientras no hay respuesta del plan el botón queda deshabilitado, sin razón que mostrar
  const disabledReason = started ? "Ya hay un rollback en curso." : plan?.reason ?? null;

  async function confirm() {
    // Se bloquea antes de la llamada: un segundo clic no puede lanzar otro rollback (CA-8)
    setBusy(true);
    setError(null);
    dialog.current?.close();
    try {
      onUpdated(await rollbackIncident(incident.id));
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function copy() {
    if (message === null) return;
    try {
      await navigator.clipboard.writeText(message);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setError("No se pudo copiar; selecciona el texto y cópialo a mano.");
    }
  }

  const current = STEPS.findIndex((step) => step.status === rollback.status);

  return (
    <section className="card" aria-label="Recuperación">
      <h2>Recuperación</h2>

      {error && (
        <p className="error" role="alert">
          ✕ {error}
        </p>
      )}

      <dl className="data">
        <dt>Versión</dt>
        <dd>
          {from && to ? (
            <strong>
              {from} → {to}
            </strong>
          ) : (
            <span className="muted">Sin versión a la que volver</span>
          )}
        </dd>
        {started && (
          <>
            <dt>Pedido por</dt>
            <dd>
              {rollback.by_name} · {formatDateTime(rollback.at)}
              {rollback.commit_url && (
                <>
                  {" · "}
                  <a href={rollback.commit_url} target="_blank" rel="noreferrer">
                    Ver commit {rollback.commit_sha?.slice(0, 8)} en Gitea ↗
                  </a>
                </>
              )}
            </dd>
          </>
        )}
        {incident.mttr_minutes !== null && (
          <>
            <dt>MTTR</dt>
            <dd>
              <strong>{formatMttr(incident.mttr_minutes)}</strong>
            </dd>
          </>
        )}
      </dl>

      {planned && (
        <div className="stacked-form">
          <button type="button" className="button" disabled={!canRollback} onClick={() => dialog.current?.showModal()}>
            Rollback
          </button>
          {!canRollback && disabledReason && <p className="muted">{disabledReason}</p>}
        </div>
      )}

      {started && (
        <ol className="progress-steps" aria-label="Avance del rollback">
          {STEPS.map((step, index) => (
            <li key={step.status} aria-current={index === current ? "step" : undefined}>
              <span aria-hidden="true">{stepIcon(index, current)}</span> {step.label}
            </li>
          ))}
        </ol>
      )}
      {started && rollback.status !== "recuperado" && (
        <p className="muted">Se vuelve a consultar cada 5 segundos; no hace falta recargar.</p>
      )}
      {rollback.status === "recuperado" && incident.status === "abierto" && (
        <p className="muted">
          Argo CD confirmó la versión, pero el monitoreo aún no ve el sitio sano. Si ya responde, puedes marcarlo como
          mitigado.
        </p>
      )}

      {mitigated && message !== null && (
        <div className="stacked-form">
          <label>
            Mensaje para el cliente
            <textarea value={message} readOnly rows={4} />
          </label>
          <button type="button" className="button button-secondary" onClick={copy}>
            {copied ? "✓ Copiado" : "Copiar"}
          </button>
          <p className="muted">Es un borrador: el Hub nunca lo envía solo; la agencia decide si lo manda.</p>
        </div>
      )}

      <dialog ref={dialog} aria-labelledby="rollback-title" className="confirm-dialog">
        <h3 id="rollback-title">¿Volver de {from} a {to}?</h3>
        <p>
          El Hub escribirá un commit en <code>hub-gitops</code> con la versión {to} y Argo CD sincronizará el sitio.
          Nadie toca el clúster. Quedará registrado a tu nombre.
        </p>
        <div className="actions">
          <button type="button" className="button" onClick={confirm} disabled={busy}>
            Confirmar rollback
          </button>
          <button type="button" className="button button-secondary" onClick={() => dialog.current?.close()}>
            Cancelar
          </button>
        </div>
      </dialog>
    </section>
  );
}
