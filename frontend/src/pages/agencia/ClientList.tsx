// Pantalla "Clientes" de la consola de agencia: tabla con servicio, plan y estado de cada cliente.
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { listClients, type ClientSummary } from "../../api";
import StatusBadge from "../../components/StatusBadge";

export default function ClientList() {
  const [clients, setClients] = useState<ClientSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listClients()
      .then(setClients)
      .catch((e: Error) => setError(e.message));
  }, []);

  return (
    <>
      <div className="page-header">
        <h1>Clientes</h1>
        <Link to="/agencia/clientes/nuevo" className="button">
          + Registrar cliente
        </Link>
      </div>

      {error && (
        <p className="error" role="alert">
          ✕ No se pudo cargar la lista: {error}
        </p>
      )}
      {!clients && !error && <p>Cargando clientes…</p>}
      {clients && clients.length === 0 && <p>Todavía no hay clientes registrados.</p>}

      {clients && clients.length > 0 && (
        <table className="table">
          <thead>
            <tr>
              <th>Cliente</th>
              <th>Servicio</th>
              <th>Plan</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            {clients.map((client) => (
              <tr key={client.id}>
                <td>
                  <strong>{client.name}</strong>
                  {client.contact_name && <div className="muted">{client.contact_name}</div>}
                </td>
                <td>
                  {client.main_service ? (
                    <>
                      {client.main_service.name}
                      <div className="muted">{client.main_service.host}</div>
                    </>
                  ) : (
                    "Sin servicio"
                  )}
                </td>
                <td>{client.main_service?.plan.name ?? "—"}</td>
                <td>{client.main_service ? <StatusBadge status={client.main_service.status} /> : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  );
}
