// Hook de las listas desplegables propias (selector, fecha y mes): coloca la lista junto a su campo, la voltea hacia arriba si abajo no cabe, la mantiene dentro de la ventana y la cierra al pulsar fuera.
import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";

export interface ListPosition {
  top: number;
  left: number;
  minWidth: number;
  maxHeight: number;
  arriba: boolean;
}

const MARGIN = 8; // distancia mínima al borde de la ventana
const GAP = 4; // espacio entre el campo y la lista

export function usePopover(abierto: boolean, cerrar: () => void, altoMaximo = 320) {
  const triggerRef = useRef<HTMLButtonElement>(null);
  const popRef = useRef<HTMLDivElement>(null);
  const [pos, setPos] = useState<ListPosition | null>(null);

  const colocar = useCallback(() => {
    const trigger = triggerRef.current;
    const lista = popRef.current;
    if (!trigger || !lista) return;
    const campo = trigger.getBoundingClientRect();
    const natural = lista.scrollHeight + 2; // altura del contenido más los dos bordes
    const debajo = window.innerHeight - campo.bottom - GAP - MARGIN;
    const encima = campo.top - GAP - MARGIN;
    const arriba = natural > debajo && encima > debajo;
    const maxHeight = Math.max(120, Math.min(altoMaximo, arriba ? encima : debajo));
    const alto = Math.min(natural, maxHeight);
    const ancho = Math.max(campo.width, lista.offsetWidth);
    const left = Math.max(MARGIN, Math.min(campo.left, window.innerWidth - ancho - MARGIN));
    const top = arriba ? campo.top - GAP - alto : campo.bottom + GAP;
    setPos({ top, left, minWidth: campo.width, maxHeight, arriba });
  }, [altoMaximo]);

  // Se mide después de pintar la lista (oculta) para saber cuánto ocupa y dónde cabe
  useLayoutEffect(() => {
    if (abierto) colocar();
    else setPos(null);
  }, [abierto, colocar]);

  useEffect(() => {
    if (!abierto) return;
    const alMover = () => colocar();
    const alPulsar = (evento: PointerEvent) => {
      const destino = evento.target as Node;
      if (triggerRef.current?.contains(destino) || popRef.current?.contains(destino)) return;
      // Pulsar el texto de la etiqueta que envuelve al campo reenvía el clic al campo: no se cierra aquí para no reabrirla enseguida
      const etiqueta = (destino as Element).closest?.("label");
      if (etiqueta && triggerRef.current && etiqueta.contains(triggerRef.current)) return;
      cerrar();
    };
    window.addEventListener("resize", alMover);
    window.addEventListener("scroll", alMover, true);
    document.addEventListener("pointerdown", alPulsar);
    return () => {
      window.removeEventListener("resize", alMover);
      window.removeEventListener("scroll", alMover, true);
      document.removeEventListener("pointerdown", alPulsar);
    };
  }, [abierto, cerrar, colocar]);

  return { triggerRef, popRef, pos };
}
