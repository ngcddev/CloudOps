// Punto de entrada del frontend: monta App dentro del enrutador del navegador.
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import "@fontsource-variable/geist";
import "@fontsource-variable/geist-mono";

import App from "./App";
import { AuthProvider } from "./auth";
import ErrorBoundary from "./components/ErrorBoundary";
import "./styles.css";

// El ErrorBoundary de fuera atrapa lo que falle fuera de un layout (Login, la sesión); los layouts llevan el suyo por pantalla (SafeOutlet)
createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ErrorBoundary>
      <BrowserRouter>
        <AuthProvider>
          <App />
        </AuthProvider>
      </BrowserRouter>
    </ErrorBoundary>
  </StrictMode>,
);
