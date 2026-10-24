// Protege un grupo de rutas: sin sesión lleva a /login y con el rol equivocado al inicio del rol propio (spec 007).
import { Navigate, Outlet, useLocation } from "react-router-dom";

import { homeFor, useAuth } from "../auth";

export default function RequireRole({ role }: { role: "agencia" | "cliente" }) {
  const { user, loading, mock } = useAuth();
  const location = useLocation();

  if (loading) return <p className="muted">Cargando…</p>;
  // Con datos de prueba no hay sesión que pedir
  if (mock) return <Outlet />;
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  if (user.role !== role) return <Navigate to={homeFor(user)} replace />;
  return <Outlet />;
}
