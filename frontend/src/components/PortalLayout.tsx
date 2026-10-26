// Marco del portal del cliente: encabezado con el nombre de quien entró y "Cerrar sesión" (spec 007).
import { Outlet } from "react-router-dom";

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
        <SessionBar />
      </header>
      <main className="content">
        <MockDataNotice />
        <Outlet />
      </main>
    </div>
  );
}
