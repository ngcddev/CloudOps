// Marco de la consola de agencia: menú lateral de navegación y área de contenido.
import { NavLink, Outlet } from "react-router-dom";

import MockDataNotice from "./MockDataNotice";

// Secciones de la consola. Las que aún no existen se muestran deshabilitadas con la spec que las trae.
const sections: { label: string; to?: string; spec?: string }[] = [
  { label: "Clientes", to: "/agencia/clientes" },
  { label: "Solicitudes", to: "/agencia/tickets" },
  { label: "Cambios", spec: "005" },
  { label: "Incidentes", spec: "008" },
  { label: "Tableros", spec: "010" },
  { label: "Reportes", spec: "013" },
];

export default function AgencyLayout() {
  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="brand">CloudOps Client Hub</div>
        <div className="brand-sub">Consola de agencia · Forja Digital</div>
        <nav aria-label="Menú de la consola">
          <ul className="nav">
            {sections.map((section) => (
              <li key={section.label}>
                {section.to ? (
                  <NavLink to={section.to}>{section.label}</NavLink>
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
      </aside>
      <main className="content">
        <MockDataNotice />
        <Outlet />
      </main>
    </div>
  );
}
