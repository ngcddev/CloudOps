// Componente raíz: define las rutas de la aplicación.
// Cada pantalla se carga en su propio archivo cuando se visita (auditoría FE-03): quien entra al portal del cliente no descarga la consola de agencia.
// Los marcos (layouts) y la entrada (Login) van con la aplicación porque se ven siempre; el «Cargando…» y el ErrorBoundary están en OutletSeguro.
import { lazy } from "react";
import { Route, Routes } from "react-router-dom";

import AgencyLayout from "./components/AgencyLayout";
import HomeRedirect from "./components/HomeRedirect";
import PortalLayout from "./components/PortalLayout";
import RequireRole from "./components/RequireRole";
import Login from "./pages/Login";
import NotFound from "./pages/NotFound";

const ClientDetail = lazy(() => import("./pages/agencia/ClientDetail"));
const ClientForm = lazy(() => import("./pages/agencia/ClientForm"));
const Assistant = lazy(() => import("./pages/agencia/Assistant"));
const Reports = lazy(() => import("./pages/agencia/Reports"));
const AuditLogList = lazy(() => import("./pages/agencia/AuditLogList"));
const ChangeList = lazy(() => import("./pages/agencia/ChangeList"));
const ClientList = lazy(() => import("./pages/agencia/ClientList"));
const ClientMetrics = lazy(() => import("./pages/agencia/ClientMetrics"));
const Dashboard = lazy(() => import("./pages/agencia/Dashboard"));
const IncidentDetail = lazy(() => import("./pages/agencia/IncidentDetail"));
const IncidentList = lazy(() => import("./pages/agencia/IncidentList"));
const ServiceList = lazy(() => import("./pages/agencia/ServiceList"));
const TicketDetail = lazy(() => import("./pages/agencia/TicketDetail"));
const TicketList = lazy(() => import("./pages/agencia/TicketList"));
const PortalReports = lazy(() => import("./pages/portal/Reports"));
const PortalTicketList = lazy(() => import("./pages/portal/TicketList"));
const PortalHome = lazy(() => import("./pages/portal/Home"));

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomeRedirect />} />
      <Route path="/login" element={<Login />} />
      <Route element={<RequireRole role="agencia" />}>
        <Route path="/agencia" element={<AgencyLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="clientes" element={<ClientList />} />
          <Route path="clientes/nuevo" element={<ClientForm />} />
          <Route path="clientes/:id" element={<ClientDetail />} />
          <Route path="clientes/:id/metricas" element={<ClientMetrics />} />
          <Route path="asistente" element={<Assistant />} />
          <Route path="reportes" element={<Reports />} />
          <Route path="bitacora" element={<AuditLogList />} />
          <Route path="cambios" element={<ChangeList />} />
          <Route path="servicios" element={<ServiceList />} />
          <Route path="incidentes" element={<IncidentList />} />
          <Route path="incidentes/:id" element={<IncidentDetail />} />
          <Route path="tickets" element={<TicketList />} />
          <Route path="tickets/:id" element={<TicketDetail />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Route>
      <Route element={<RequireRole role="cliente" />}>
        <Route path="/portal" element={<PortalLayout />}>
          <Route index element={<PortalHome />} />
          <Route path="solicitudes" element={<PortalTicketList />} />
          <Route path="reportes" element={<PortalReports />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Route>
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
