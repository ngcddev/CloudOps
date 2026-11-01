// Marco del portal del cliente: menú con «Inicio», «Solicitudes» (spec 010, T17) y «Reportes» (spec 013), y la
// sesión (spec 007).
import { NavLink, Outlet } from "react-router-dom";

import Logo from "./Logo";
import MockDataNotice from "./MockDataNotice";
import SessionBar from "./SessionBar";

export default function PortalLayout() {
  return (
    <div className="portal">
      <header className="portal-header">
        <div className="brand">
          <Logo />
          Forja Digital · Portal de clientes
        </div>
        <nav className="portal-nav" aria-label="Menú del portal">
          <NavLink to="/portal" end>
            Inicio
          </NavLink>
          <NavLink to="/portal/solicitudes">Solicitudes</NavLink>
          <NavLink to="/portal/reportes">Reportes</NavLink>
        </nav>
        <SessionBar />
      </header>
      <main className="content">
        <MockDataNotice />
        <Outlet />
      </main>
    </div>
  );
}
