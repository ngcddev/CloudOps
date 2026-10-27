// Componente raíz: define las rutas de la aplicación.
import { Navigate, Route, Routes } from "react-router-dom";

import AgencyLayout from "./components/AgencyLayout";
import HomeRedirect from "./components/HomeRedirect";
import PortalLayout from "./components/PortalLayout";
import RequireRole from "./components/RequireRole";
import ClientDetail from "./pages/agencia/ClientDetail";
import ClientForm from "./pages/agencia/ClientForm";
import AuditLogList from "./pages/agencia/AuditLogList";
import ChangeList from "./pages/agencia/ChangeList";
import ClientList from "./pages/agencia/ClientList";
import Dashboard from "./pages/agencia/Dashboard";
import IncidentDetail from "./pages/agencia/IncidentDetail";
import IncidentList from "./pages/agencia/IncidentList";
import ServiceList from "./pages/agencia/ServiceList";
import TicketDetail from "./pages/agencia/TicketDetail";
import TicketList from "./pages/agencia/TicketList";
import PortalTicketList from "./pages/portal/TicketList";
import Login from "./pages/Login";
import NotFound from "./pages/NotFound";

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
          <Route index element={<Navigate to="solicitudes" replace />} />
          <Route path="solicitudes" element={<PortalTicketList />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Route>
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
