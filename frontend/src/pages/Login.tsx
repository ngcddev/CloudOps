// Pantalla de inicio de sesión: correo y contraseña; lleva a la consola o al portal según el rol (spec 007).
import { useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";

import { homeFor, useAuth } from "../auth";
import Logo from "../components/Logo";
import ThemeToggle from "../components/ThemeToggle";

export default function Login() {
  const { user, loading, mock, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (loading) return <p className="muted">Cargando…</p>;
  if (mock) return <Navigate to="/agencia/clientes" replace />;
  if (user) return <Navigate to={homeFor(user)} replace />;

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const signedIn = await login(email, password);
      // Si venía de una pantalla de su rol, vuelve a ella; si no, va a su inicio
      const from = (location.state as { from?: string } | null)?.from;
      const home = homeFor(signedIn);
      navigate(from && from.startsWith(home) ? from : home, { replace: true });
    } catch (loginError) {
      setError((loginError as Error).message);
      setSubmitting(false);
    }
  }

  return (
    <main className="login">
      <div className="login-theme">
        <ThemeToggle />
      </div>
      <section className="card login-card">
        <Logo size={28} />
        <p className="eyebrow">Centro de operación</p>
        <h1>CloudOps Client Hub</h1>
        <p className="muted">Entra con tu correo y tu contraseña.</p>
        <form onSubmit={handleSubmit} className="stacked-form">
          <label>
            <span>Correo</span>
            <input
              type="email"
              autoComplete="username"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </label>
          <label>
            <span>Contraseña</span>
            <input
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </label>
          {error && (
            <p role="alert" className="error">
              ✗ {error}
            </p>
          )}
          <button type="submit" className="button button-primary" disabled={submitting}>
            {submitting ? "Entrando…" : "Entrar"}
          </button>
        </form>
      </section>
    </main>
  );
}
