// Bandeja de solicitudes de cambio: aprobar o rechazar y seguir la publicación (spec 005, T18).
import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import SecurityChecks, { gateSummary } from "../../components/SecurityChecks";
import {
  approveChangeRequest,
  getChangeGate,
  listChangeRequests,
  listServicesStatus,
  rejectChangeRequest,
  type ChangeRequest,
  type Gate,
  type ChangeStatus,
  type ServiceVersionStatus,
} from "../../api";
import { formatDateTime } from "../../format";

// Texto de la interfaz de cada estado (glosario), con ícono: el estado nunca se comunica con color
const STATUS_TEXT: Record<ChangeStatus, { icon: string; text: string }> = {
  pendiente: { icon: "…", text: "Pendiente" },
  aprobada: { icon: "✓", text: "Aprobada" },
  en_validacion: { icon: "⟳", text: "En validación" },
  desplegada: { icon: "✓", text: "Publicada" },
  rechazada: { icon: "✕", text: "Rechazada" },
  fallida: { icon: "!", text: "No se pudo publicar" },
};

// Mientras un cambio espera a Argo CD la bandeja se vuelve a leer sola
const REFRESH_MS = 5000;

export default function ChangeList() {
  const [changes, setChanges] = useState<ChangeRequest[] | null>(null);
  const [services, setServices] = useState<ServiceVersionStatus[]>([]);
  // Puerta de seguridad de la versión destino de cada cambio (spec 006)
  const [gates, setGates] = useState<Map<number, Gate>>(new Map());
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [rejecting, setRejecting] = useState<number | null>(null);
  const [reason, setReason] = useState("");

  const load = useCallback(async () => {
    try {
      const [changeData, serviceData] = await Promise.all([listChangeRequests(), listServicesStatus()]);
      // Si la puerta de un cambio no se puede leer, ese cambio queda sin controles pero la bandeja sigue
      const gateResults = await Promise.allSettled(changeData.map((change) => getChangeGate(change.id)));
      setChanges(changeData);
      setServices(serviceData);
      setGates(
        new Map(
          changeData.flatMap((change, index) => {
            const result = gateResults[index];
            return result.status === "fulfilled" ? [[change.id, result.value] as [number, Gate]] : [];
          }),
        ),
      );
      setError(null);
    } catch (loadError) {
      setError((loadError as Error).message);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  // Se vuelve a leer mientras algo está en camino: una publicación o los controles de seguridad corriendo
  const waiting =
    changes?.some((change) => change.status === "en_validacion" || change.status === "aprobada") ||
    changes?.some((change) => change.status === "pendiente" && gates.get(change.id)?.status === "en_curso");
  useEffect(() => {
    if (!waiting) return;
    const timer = window.setInterval(() => void load(), REFRESH_MS);
    return () => window.clearInterval(timer);
  }, [waiting, load]);

  const serviceById = useMemo(() => new Map(services.map((s) => [s.service_id, s])), [services]);

  async function handleApprove(change: ChangeRequest) {
    setBusyId(change.id);
    try {
      await approveChangeRequest(change.id);
      setError(null);
      await load();
    } catch (actionError) {
      setError((actionError as Error).message);
    } finally {
      setBusyId(null);
    }
  }

  async function handleReject(event: React.FormEvent, change: ChangeRequest) {
    event.preventDefault();
    setBusyId(change.id);
    try {
      await rejectChangeRequest(change.id, reason);
      setRejecting(null);
      setReason("");
      setError(null);
      await load();
    } catch (actionError) {
      setError((actionError as Error).message);
    } finally {
      setBusyId(null);
    }
  }

  return (
    <>
      <div className="page-header">
        <h1>Cambios</h1>
      </div>

      {error && (
        <p className="error" role="alert">
          ✕ {error}
        </p>
      )}

      {!changes && !error && <p>Cargando cambios…</p>}

      {changes && changes.length === 0 && (
        <p>
          No hay solicitudes de cambio. Se registran desde el detalle de una <Link to="/agencia/tickets">solicitud</Link>{" "}
          de tipo cambio.
        </p>
      )}

      {changes && changes.length > 0 && (
        <table className="table">
          <thead>
            <tr>
              <th>Cliente</th>
              <th>Cambio</th>
              <th>Versión</th>
              <th>Estado</th>
              <th>Seguridad</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {changes.map((change) => {
              const service = serviceById.get(change.service_id);
              const status = STATUS_TEXT[change.status];
              const gate = gates.get(change.id);
              const canApprove = gate?.status === "ok";
              return (
                <tr key={change.id}>
                  <td>
                    <strong>{service?.client_name ?? "Cliente"}</strong>
                    <div className="muted">{service?.service_name ?? "Servicio"}</div>
                  </td>
                  <td>
                    <Link to={`/agencia/tickets/${change.ticket_id}`}>
                      <strong>{change.ticket_title ?? `Solicitud #${change.ticket_id}`}</strong>
                    </Link>
                    <div className="muted">
                      Pedido el {formatDateTime(change.created_at)}
                      {change.requested_by_name ? ` por ${change.requested_by_name}` : ""}
                    </div>
                  </td>
                  <td>
                    {change.from_version} → <strong>{change.to_version}</strong>
                  </td>
                  <td>
                    <span className={`status-pill change-${change.status}`}>
                      <span aria-hidden="true">{status.icon}</span> {status.text}
                    </span>
                    {change.approved_at && (
                      <div className="muted">
                        {change.approved_by_name ?? "Usuario"} · {formatDateTime(change.approved_at)}
                      </div>
                    )}
                    {change.deployed_at && <div className="muted">Publicada {formatDateTime(change.deployed_at)}</div>}
                    {change.rejection_reason && <div className="muted">Motivo: {change.rejection_reason}</div>}
                  </td>
                  <td>{gate ? <SecurityChecks gate={gate} /> : <span className="muted">—</span>}</td>
                  <td>
                    {change.status === "pendiente" && rejecting !== change.id && (
                      <div className="form-actions">
                        <button
                          type="button"
                          className="button"
                          disabled={busyId === change.id || !canApprove}
                          title={canApprove || !gate ? undefined : gateSummary(gate.status, gate.failed_step)}
                          onClick={() => void handleApprove(change)}
                        >
                          Aprobar
                        </button>
                        <button
                          type="button"
                          className="button button-secondary"
                          disabled={busyId === change.id}
                          onClick={() => {
                            setRejecting(change.id);
                            setReason("");
                          }}
                        >
                          Rechazar
                        </button>
                      </div>
                    )}
                    {change.status === "pendiente" && rejecting === change.id && (
                      <form onSubmit={(event) => void handleReject(event, change)} className="stacked-form">
                        <label>
                          <span>Motivo del rechazo</span>
                          <textarea
                            rows={2}
                            value={reason}
                            required
                            onChange={(event) => setReason(event.target.value)}
                          />
                        </label>
                        <div className="form-actions">
                          <button type="submit" className="button" disabled={busyId === change.id}>
                            Confirmar rechazo
                          </button>
                          <button type="button" className="button button-secondary" onClick={() => setRejecting(null)}>
                            Cancelar
                          </button>
                        </div>
                      </form>
                    )}
                    {change.status === "pendiente" && rejecting !== change.id && gate && !canApprove && (
                      <div className="muted">Se puede aprobar cuando los controles de seguridad pasen.</div>
                    )}
                    {change.status !== "pendiente" && <span className="muted">—</span>}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </>
  );
}
