// Componente raíz: define las rutas de la aplicación.
import { Navigate, Route, Routes } from "react-router-dom";

import AgencyLayout from "./components/AgencyLayout";
import ClientList from "./pages/agencia/ClientList";
import NotFound from "./pages/NotFound";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/agencia/clientes" replace />} />
      <Route path="/agencia" element={<AgencyLayout />}>
        <Route index element={<Navigate to="clientes" replace />} />
        <Route path="clientes" element={<ClientList />} />
        <Route path="*" element={<NotFound />} />
      </Route>
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
