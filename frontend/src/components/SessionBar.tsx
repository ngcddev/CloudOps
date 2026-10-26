// Quién tiene la sesión abierta: inicial, nombre, cambio de tema y "Cerrar sesión" (spec 007).
// Lo usan el menú de la consola y el encabezado del portal.
import { useNavigate } from "react-router-dom";

import { useAuth } from "../auth";
import ThemeToggle from "./ThemeToggle";

export default function SessionBar() {
  const { user, mock, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <div className="session">
      <div className="session-user">
        <span className="avatar" aria-hidden="true">
          {user?.name.trim().charAt(0).toUpperCase()}
        </span>
        <span className="session-name">{user?.name}</span>
      </div>
      <div className="session-actions">
        <ThemeToggle />
        {!mock && (
          <button type="button" className="button button-secondary" onClick={handleLogout}>
            Cerrar sesión
          </button>
        )}
      </div>
    </div>
  );
}
