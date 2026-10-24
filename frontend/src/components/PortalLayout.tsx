// Marco del portal del cliente: encabezado con el nombre de quien entró y "Cerrar sesión" (spec 007).
import { Outlet, useNavigate } from "react-router-dom";

import { useAuth } from "../auth";
import MockDataNotice from "./MockDataNotice";

export default function PortalLayout() {
  const { user, mock, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <div className="portal">
      <header className="portal-header">
        <div className="brand">Forja Digital · Portal de clientes</div>
        <div className="session">
          <span>{user?.name}</span>
          {!mock && (
            <button type="button" className="button button-secondary" onClick={handleLogout}>
              Cerrar sesión
            </button>
          )}
        </div>
      </header>
      <main className="content">
        <MockDataNotice />
        <Outlet />
      </main>
    </div>
  );
}
