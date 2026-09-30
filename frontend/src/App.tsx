// Componente raíz: define las rutas de la aplicación.
import { Navigate, Route, Routes } from "react-router-dom";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/agencia/clientes" replace />} />
      <Route path="/agencia/clientes" element={<h1>Clientes</h1>} />
    </Routes>
  );
}
