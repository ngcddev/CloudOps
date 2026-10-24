// Sesión de la persona usuaria: guarda el token mientras dure la pestaña y lo entrega a la API (spec 007).
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import {
  getMe,
  isUsingMockData,
  listClients,
  login as apiLogin,
  setAuthToken,
  setUnauthorizedHandler,
  type SessionUser,
} from "./api";

const STORAGE_KEY = "hub.session";

interface AuthState {
  user: SessionUser | null;
  // true mientras se decide si hay API y se valida una sesión guardada
  loading: boolean;
  // true cuando no hay API y la interfaz trabaja con datos de prueba (no se pide iniciar sesión)
  mock: boolean;
  login: (email: string, password: string) => Promise<SessionUser>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

// sessionStorage puede no estar disponible (ventana privada, datos bloqueados): la sesión sigue en memoria
function readToken(): string | null {
  try {
    return sessionStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

function writeToken(token: string | null) {
  try {
    if (token) sessionStorage.setItem(STORAGE_KEY, token);
    else sessionStorage.removeItem(STORAGE_KEY);
  } catch {
    // Sin almacenamiento: al recargar la página se pedirá entrar de nuevo
  }
}

// A dónde lleva cada rol al entrar
export function homeFor(user: SessionUser): string {
  return user.role === "agencia" ? "/agencia" : "/portal";
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<SessionUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [mock, setMock] = useState(false);

  const clear = useCallback(() => {
    setAuthToken(null);
    writeToken(null);
    setUser(null);
  }, []);

  useEffect(() => {
    setUnauthorizedHandler(clear);
    let cancelled = false;

    async function start() {
      if (await isUsingMockData()) {
        // Sin API: una técnica de ejemplo, ligada al primer cliente de los datos de prueba
        const clients = await listClients();
        if (cancelled) return;
        setMock(true);
        setUser({
          id: 1,
          name: "Sofía Ramírez",
          email: "sofia@forjadigital.test",
          role: "agencia",
          client_id: clients[0]?.id ?? null,
        });
        setLoading(false);
        return;
      }
      const token = readToken();
      if (token) {
        setAuthToken(token);
        try {
          const me = await getMe();
          if (!cancelled) setUser(me);
        } catch {
          if (!cancelled) clear();
        }
      }
      if (!cancelled) setLoading(false);
    }

    void start();
    return () => {
      cancelled = true;
      setUnauthorizedHandler(null);
    };
  }, [clear]);

  const login = useCallback(async (email: string, password: string) => {
    const result = await apiLogin(email, password);
    setAuthToken(result.access_token);
    writeToken(result.access_token);
    setUser(result.user);
    return result.user;
  }, []);

  const value = useMemo<AuthState>(
    () => ({ user, loading, mock, login, logout: clear }),
    [user, loading, mock, login, clear],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth debe usarse dentro de AuthProvider.");
  return context;
}
