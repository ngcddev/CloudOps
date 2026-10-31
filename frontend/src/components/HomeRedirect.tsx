// Ruta "/": lleva a cada persona a su inicio, o a /login si aún no ha entrado (spec 007).
import { Navigate } from "react-router-dom";

import { homeFor, useAuth } from "../auth";

export default function HomeRedirect() {
  const { user, loading, mock } = useAuth();

  if (loading) return <p className="muted">Cargando…</p>;
  if (mock) return <Navigate to="/agencia" replace />;
  return <Navigate to={user ? homeFor(user) : "/login"} replace />;
}
