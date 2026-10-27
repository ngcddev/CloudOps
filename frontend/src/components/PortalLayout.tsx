// Marco del portal del cliente: encabezado con el nombre de quien entró y "Cerrar sesión" (spec 007).
// Menú con «Inicio» y «Solicitudes» (spec 010, T17).
import { NavLink, Outlet, useNavigate } from "react-router-dom";

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
        <nav className="portal-nav" aria-label="Menú del portal">
          <NavLink to="/portal" end>
            Inicio
          </NavLink>
          <NavLink to="/portal/solicitudes">Solicitudes</NavLink>
        </nav>
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
