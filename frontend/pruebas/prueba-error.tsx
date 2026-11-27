// Prueba en un DOM real (jsdom) del ErrorBoundary y de SafeOutlet (spec 022, T11): un error de render no deja la pantalla en blanco ni se lleva el marco,
// y una pantalla que se carga bajo demanda muestra «Cargando…». La corre frontend/pruebas/error-boundary.sh; no forma parte de `npm run build`.
import { StrictMode, act, lazy, type ReactElement } from "react";
import { createRoot } from "react-dom/client";
import { Link, MemoryRouter, Route, Routes } from "react-router-dom";

import ErrorBoundary from "../src/components/ErrorBoundary";
import SafeOutlet from "../src/components/SafeOutlet";

(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

let falla = true;
function Condicional(): ReactElement {
  if (falla) throw new Error("falla de prueba");
  return <p id="ok">pantalla bien</p>;
}

const fallos: string[] = [];
function ok(condicion: boolean, mensaje: string) {
  console.log((condicion ? "✓ " : "✗ ") + mensaje);
  if (!condicion) fallos.push(mensaje);
}

function montar(elemento: ReactElement) {
  const contenedor = document.createElement("div");
  document.body.appendChild(contenedor);
  const raiz = createRoot(contenedor);
  act(() => raiz.render(<StrictMode>{elemento}</StrictMode>));
  return { contenedor, raiz };
}

async function main() {
  const silencio = console.error;
  console.error = () => {}; // React y el ErrorBoundary escriben el error esperado: no ensuciar la salida

  // 1. Un error de render muestra el aviso, no deja la pantalla en blanco, y «Reintentar» lo recupera
  falla = true;
  const a = montar(
    <ErrorBoundary>
      <Condicional />
    </ErrorBoundary>,
  );
  ok(a.contenedor.querySelector("[role=alert]") !== null, "un error de render muestra un aviso con role=alert");
  ok((a.contenedor.textContent ?? "").includes("Algo salió mal"), "el aviso dice qué pasó, en español");
  ok(a.contenedor.querySelector("#ok") === null, "la pantalla rota no se muestra");
  falla = false;
  const reintentar = [...a.contenedor.querySelectorAll("button")].find((b) => b.textContent === "Reintentar");
  ok(reintentar !== undefined, "hay un botón «Reintentar»");
  act(() => reintentar!.click());
  ok(a.contenedor.querySelector("#ok") !== null && a.contenedor.querySelector("[role=alert]") === null, "«Reintentar» recupera la pantalla cuando el error pasó");
  act(() => a.raiz.unmount());

  // 2. En un layout el error no se lleva el marco, y al cambiar de ruta se descarta solo
  falla = true;
  const b = montar(
    <MemoryRouter initialEntries={["/a"]}>
      <nav id="marco">
        <Link id="ir-b" to="/b">
          ir a b
        </Link>
      </nav>
      <Routes>
        <Route element={<SafeOutlet />}>
          <Route path="/a" element={<Condicional />} />
          <Route path="/b" element={<p id="b">pantalla b</p>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  );
  ok(b.contenedor.querySelector("#marco") !== null, "el marco (menú) sigue en pantalla aunque la pantalla falle");
  ok(b.contenedor.querySelector("[role=alert]") !== null, "el aviso aparece dentro del área de contenido");
  act(() => (b.contenedor.querySelector("#ir-b") as HTMLElement).click());
  ok(b.contenedor.querySelector("#b") !== null && b.contenedor.querySelector("[role=alert]") === null, "al navegar a otra pantalla el error se descarta solo");
  act(() => b.raiz.unmount());

  // 3. Una pantalla que se carga bajo demanda muestra «Cargando…» y luego su contenido
  let resolver!: (modulo: { default: () => ReactElement }) => void;
  const Perezosa = lazy(() => new Promise<{ default: () => ReactElement }>((r) => (resolver = r)));
  const c = montar(
    <MemoryRouter initialEntries={["/p"]}>
      <Routes>
        <Route element={<SafeOutlet />}>
          <Route path="/p" element={<Perezosa />} />
        </Route>
      </Routes>
    </MemoryRouter>,
  );
  ok((c.contenedor.querySelector("[role=status]")?.textContent ?? "") === "Cargando…", "mientras llega la pantalla se ve «Cargando…» con role=status");
  await act(async () => resolver({ default: () => <p id="cargada">pantalla cargada</p> }));
  ok(c.contenedor.querySelector("#cargada") !== null && c.contenedor.querySelector("[role=status]") === null, "cuando llega, se muestra la pantalla y desaparece el «Cargando…»");

  console.error = silencio;
  console.log(fallos.length === 0 ? "\nTODO EN VERDE" : `\nFALLÓ: ${fallos.length}`);
  process.exit(fallos.length === 0 ? 0 : 1);
}

void main();
