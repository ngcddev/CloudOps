// Consola de servicios: por cliente, versión activa, sincronización, salud y último autor (spec 005, T20).
import { Fragment, useCallback, useEffect, useState } from "react";

import {
  listDeployments,
  listServicesStatus,
  type ChangeStatus,
  type Deployment,
  type ServiceVersionStatus,
} from "../../api";
import { formatDateTime } from "../../format";

// Lo que informa Argo CD, en texto de la consola con ícono (el estado nunca se comunica con color)
const SYNC_TEXT: Record<string, string> = {
  Synced: "✓ Sincronizado",
  OutOfSync: "⟳ Sin sincronizar",
  Unknown: "? Sin información",
};

const HEALTH_TEXT: Record<string, string> = {
  Healthy: "✓ Sano",
  Progressing: "⟳ Iniciando",
  Degraded: "! Con fallas",
  Missing: "✕ No encontrado",
  Suspended: "Ⅱ Pausado",
  Unknown: "? Sin información",
};

const CHANGE_TEXT: Record<ChangeStatus, string> = {
  pendiente: "pendiente de aprobación",
  aprobada: "aprobada",
  en_validacion: "en validación",
  desplegada: "publicada",
  rechazada: "rechazada",
  fallida: "no se pudo publicar",
};

// Estado de los sitios en vivo: se vuelve a leer cada tanto
const REFRESH_MS = 10000;

export default function ServiceList() {
  const [rows, setRows] = useState<ServiceVersionStatus[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<{ serviceId: number; items: Deployment[] } | null>(null);

  const load = useCallback(async () => {
    try {
      setRows(await listServicesStatus());
      setError(null);
    } catch (loadError) {
      setError((loadError as Error).message);
    }
  }, []);

  useEffect(() => {
    void load();
    const timer = window.setInterval(() => void load(), REFRESH_MS);
    return () => window.clearInterval(timer);
  }, [load]);

  async function toggleHistory(serviceId: number) {
    if (history?.serviceId === serviceId) {
      setHistory(null);
      return;
    }
    try {
      setHistory({ serviceId, items: await listDeployments(serviceId) });
    } catch (historyError) {
      setError((historyError as Error).message);
    }
  }

  return (
    <>
      <div className="page-header">
        <h1>Servicios</h1>
      </div>

      {error && (
        <p className="error" role="alert">
          ✕ No se pudo cargar el estado: {error}
        </p>
      )}
      {!rows && !error && <p>Cargando servicios…</p>}

      {rows && (
        <table className="table">
          <thead>
            <tr>
              <th>Cliente</th>
              <th>Versión activa</th>
              <th>Sincronización</th>
              <th>Salud</th>
              <th>Último cambio</th>
              <th>Historial</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <Fragment key={row.service_id}>
                <tr>
                  <td>
                    <strong>{row.client_name}</strong>
                    <div className="muted">{row.host}</div>
                  </td>
                  <td>
                    <strong>{row.current_version}</strong>
                    {row.stable_version !== row.current_version && (
                      <div className="muted">Última estable: {row.stable_version}</div>
                    )}
                    {row.open_change_status && (
                      <div className="muted">
                        Cambio a {row.open_change_to_version} {CHANGE_TEXT[row.open_change_status]}
                      </div>
                    )}
                  </td>
                  <td>{SYNC_TEXT[row.sync_status] ?? row.sync_status}</td>
                  <td>{HEALTH_TEXT[row.health_status] ?? row.health_status}</td>
                  <td>
                    {row.last_author ? (
                      <>
                        {row.last_author}
                        <div className="muted">{formatDateTime(row.last_change_at)}</div>
                      </>
                    ) : (
                      <span className="muted">Sin cambios</span>
                    )}
                  </td>
                  <td>
                    <button
                      type="button"
                      className="button button-secondary"
                      aria-expanded={history?.serviceId === row.service_id}
                      onClick={() => void toggleHistory(row.service_id)}
                    >
                      {history?.serviceId === row.service_id ? "Ocultar" : "Ver"}
                    </button>
                  </td>
                </tr>
                {history?.serviceId === row.service_id && (
                  <tr>
                    <td colSpan={6}>
                      {history.items.length === 0 ? (
                        <span className="muted">Este sitio todavía no tiene cambios publicados.</span>
                      ) : (
                        <ul className="history-list">
                          {history.items.map((item) => (
                            <li key={item.id}>
                              <strong>{item.version}</strong> · {item.author}
                              <div className="muted">
                                {formatDateTime(item.created_at)}
                                {item.commit_sha ? ` · commit ${item.commit_sha.slice(0, 7)}` : ""}
                                {item.source === "rollback" ? " · restauración" : ""}
                              </div>
                            </li>
                          ))}
                        </ul>
                      )}
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
          </tbody>
        </table>
      )}
    </>
  );
}
