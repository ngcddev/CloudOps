// Sondeo periódico que respeta la pestaña (spec 022, T35; auditoría FE-09): repite `tarea` cada `cadaMs` solo mientras la pestaña está visible y, al volver a mostrarse,
// lee de inmediato. Antes cada pantalla tenía su `setInterval` y seguía consultando la API con la pestaña oculta (consumo de API y de batería).
import { useEffect, useRef } from "react";

export function useSondeo(tarea: () => void, cadaMs: number, activo = true): void {
  // Siempre se llama a la versión vigente de la tarea sin reiniciar el temporizador cada vez que cambia
  const vigente = useRef(tarea);
  vigente.current = tarea;

  useEffect(() => {
    if (!activo) return;
    const tic = () => {
      if (!document.hidden) vigente.current();
    };
    const temporizador = window.setInterval(tic, cadaMs);
    document.addEventListener("visibilitychange", tic);
    return () => {
      window.clearInterval(temporizador);
      document.removeEventListener("visibilitychange", tic);
    };
  }, [cadaMs, activo]);
}
