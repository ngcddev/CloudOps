// Área de contenido de un layout: cada pantalla se carga en su propio archivo (mientras llega, «Cargando…») y un error de render no se lleva el marco
// (menú y sesión). Al cambiar de ruta el error se descarta solo (auditoría FE-03 y FE-04).
import { Suspense } from "react";
import { Outlet, useLocation } from "react-router-dom";

import ErrorBoundary from "./ErrorBoundary";

export default function OutletSeguro() {
  const { pathname } = useLocation();
  return (
    <ErrorBoundary key={pathname}>
      <Suspense
        fallback={
          <p className="muted" role="status">
            Cargando…
          </p>
        }
      >
        <Outlet />
      </Suspense>
    </ErrorBoundary>
  );
}
