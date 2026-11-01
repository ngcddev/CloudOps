// Marco de la consola de agencia: menú lateral de navegación y área de contenido.
import { NavLink, Outlet } from "react-router-dom";

import Logo from "./Logo";
import MockDataNotice from "./MockDataNotice";
import SessionBar from "./SessionBar";

// Secciones de la consola. Las que aún no existen se muestran deshabilitadas con la spec que las trae.
const sections: { label: string; to?: string; spec?: string }[] = [
  { label: "Inicio", to: "/agencia" },
  { label: "Clientes", to: "/agencia/clientes" },
  { label: "Solicitudes", to: "/agencia/tickets" },
  { label: "Cambios", to: "/agencia/cambios" },
  { label: "Servicios", to: "/agencia/servicios" },
  { label: "Incidentes", to: "/agencia/incidentes" },
  { label: "Reportes", to: "/agencia/reportes" },
  { label: "Bitácora", to: "/agencia/bitacora" },
];

export default function AgencyLayout() {
  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="brand">
          <Logo />
          CloudOps Client Hub
        </div>
        <div className="brand-sub">Consola · Forja Digital</div>
        <nav aria-label="Menú de la consola">
          <ul className="nav">
            {sections.map((section) => (
              <li key={section.label}>
                {section.to ? (
                  <NavLink to={section.to} end={section.to === "/agencia"}>
                    {section.label}
                  </NavLink>
                ) : (
                  <span className="nav-disabled" aria-disabled="true">
                    {section.label}
                    <small>Próximamente (spec {section.spec})</small>
                  </span>
                )}
              </li>
            ))}
          </ul>
        </nav>
        <SessionBar />
      </aside>
      <main className="content">
        <MockDataNotice />
        <Outlet />
      </main>
    </div>
  );
}
