// Selector propio: reemplaza al <select> nativo, cuya lista abierta no se puede estilizar. Acepta los mismos <option> como hijos y avisa el cambio con un evento que trae target.value, así las pantallas lo siguen leyendo igual. Se maneja con el teclado (flechas, Inicio, Fin, Enter, Esc y la primera letra) y con lector de pantalla.
import { Children, Fragment, isValidElement, useCallback, useEffect, useId, useMemo, useRef, useState } from "react";
import type { ChangeEvent, KeyboardEvent, ReactNode } from "react";
import { createPortal } from "react-dom";
import { usePopover } from "../hooks/usePopover";
import { CheckIcono, FlechaIcono } from "./IconosCampo";

interface Opcion {
  value: string;
  label: string;
  disabled: boolean;
}

// Evento mínimo que reciben los manejadores: lo único que las pantallas leen es target.value (y name)
export function eventoDeCambio<T extends HTMLElement>(value: string, name = ""): ChangeEvent<T> {
  const destino = { value, name };
  return { target: destino, currentTarget: destino, type: "change" } as unknown as ChangeEvent<T>;
}

function textoDe(nodo: ReactNode): string {
  if (nodo === null || nodo === undefined || typeof nodo === "boolean") return "";
  if (typeof nodo === "string" || typeof nodo === "number") return String(nodo);
  if (Array.isArray(nodo)) return nodo.map(textoDe).join("");
  if (isValidElement(nodo)) return textoDe((nodo.props as { children?: ReactNode }).children);
  return "";
}

function opcionesDe(hijos: ReactNode): Opcion[] {
  const lista: Opcion[] = [];
  Children.forEach(hijos, (hijo) => {
    if (!isValidElement(hijo)) return;
    const props = hijo.props as { value?: string | number; children?: ReactNode; disabled?: boolean };
    if (hijo.type === Fragment) {
      lista.push(...opcionesDe(props.children));
    } else if (hijo.type === "option") {
      const label = textoDe(props.children).trim();
      lista.push({ value: props.value === undefined ? label : String(props.value), label, disabled: Boolean(props.disabled) });
    }
  });
  return lista;
}

// Sin tildes ni mayúsculas, para buscar con la primera letra
const normalizar = (texto: string) => texto.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();

export interface SelectProps {
  value: string | number;
  onChange: (evento: ChangeEvent<HTMLSelectElement>) => void;
  children: ReactNode;
  id?: string;
  name?: string;
  disabled?: boolean;
  required?: boolean;
  className?: string;
  placeholder?: string;
  "aria-label"?: string;
  "aria-labelledby"?: string;
  "aria-invalid"?: boolean | "true" | "false";
  "aria-describedby"?: string;
}

export function Select({ value, onChange, children, id, name, disabled, required, className, placeholder = "Seleccionar", ...aria }: SelectProps) {
  const opciones = useMemo(() => opcionesDe(children), [children]);
  const actual = String(value);
  const indiceActual = opciones.findIndex((opcion) => opcion.value === actual);
  const [abierto, setAbierto] = useState(false);
  const [activo, setActivo] = useState(-1);
  const cerrar = useCallback(() => setAbierto(false), []);
  const { triggerRef, popRef, pos } = usePopover(abierto, cerrar);
  const listaId = useId();
  const busqueda = useRef({ texto: "", cuando: 0 });

  const habilitadas = useMemo(() => opciones.flatMap((opcion, i) => (opcion.disabled ? [] : [i])), [opciones]);

  const abrir = () => {
    if (disabled || habilitadas.length === 0) return;
    setActivo(indiceActual >= 0 && !opciones[indiceActual].disabled ? indiceActual : habilitadas[0]);
    setAbierto(true);
  };

  const cambiarA = (i: number) => {
    const opcion = opciones[i];
    if (opcion && !opcion.disabled && opcion.value !== actual) onChange(eventoDeCambio<HTMLSelectElement>(opcion.value, name));
  };

  const elegir = (i: number) => {
    setAbierto(false);
    triggerRef.current?.focus();
    cambiarA(i);
  };

  // La opción activa siempre queda a la vista dentro de la lista
  useEffect(() => {
    if (abierto && activo >= 0) document.getElementById(`${listaId}-${activo}`)?.scrollIntoView({ block: "nearest" });
  }, [abierto, activo, listaId]);

  const mover = (delta: 1 | -1) => {
    const posicion = habilitadas.indexOf(activo);
    const siguiente = posicion === -1 ? (delta === 1 ? 0 : habilitadas.length - 1) : Math.min(habilitadas.length - 1, Math.max(0, posicion + delta));
    setActivo(habilitadas[siguiente]);
  };

  const alTeclear = (evento: KeyboardEvent<HTMLButtonElement>) => {
    if (habilitadas.length === 0) return;
    switch (evento.key) {
      case "ArrowDown":
      case "ArrowUp":
        evento.preventDefault();
        if (!abierto) abrir();
        else mover(evento.key === "ArrowDown" ? 1 : -1);
        return;
      case "Home":
      case "End":
        if (!abierto) return;
        evento.preventDefault();
        setActivo(evento.key === "Home" ? habilitadas[0] : habilitadas[habilitadas.length - 1]);
        return;
      case "Enter":
      case " ":
        evento.preventDefault();
        if (!abierto) abrir();
        else if (activo >= 0) elegir(activo);
        return;
      case "Escape":
        if (abierto) {
          evento.preventDefault();
          evento.stopPropagation();
          cerrar();
        }
        return;
      case "Tab":
        if (abierto) cerrar();
        return;
    }
    // Primera letra (o varias seguidas): salta a la opción que empieza así, como el selector nativo
    if (evento.key.length === 1 && !evento.ctrlKey && !evento.metaKey && !evento.altKey) {
      const ahora = Date.now();
      const texto = (ahora - busqueda.current.cuando < 700 ? busqueda.current.texto : "") + normalizar(evento.key);
      busqueda.current = { texto, cuando: ahora };
      const referencia = habilitadas.indexOf(abierto ? activo : indiceActual);
      const orden = [...habilitadas.slice(referencia + 1), ...habilitadas.slice(0, referencia + 1)];
      const hallada = orden.find((i) => normalizar(opciones[i].label).startsWith(texto));
      if (hallada === undefined) return;
      evento.preventDefault();
      if (abierto) setActivo(hallada);
      else cambiarA(hallada);
    }
  };

  return (
    <>
      <div className="campo-envoltura">
        <button
          type="button"
          ref={triggerRef}
          id={id}
          className={`campo-disparador${className ? ` ${className}` : ""}`}
          role="combobox"
          aria-haspopup="listbox"
          aria-expanded={abierto}
          aria-required={required || undefined}
          aria-controls={abierto ? listaId : undefined}
          aria-activedescendant={abierto && activo >= 0 ? `${listaId}-${activo}` : undefined}
          disabled={disabled}
          onClick={() => (abierto ? cerrar() : abrir())}
          onKeyDown={alTeclear}
          {...aria}
        >
          <span className={`campo-valor${indiceActual < 0 ? " campo-vacio" : ""}`}>{indiceActual >= 0 ? opciones[indiceActual].label : placeholder}</span>
          <FlechaIcono />
        </button>
        {/* Un botón no se valida solo: este campo oculto hace que "obligatorio" siga frenando el envío del formulario, con el aviso del navegador junto al selector */}
        {required && <input className="campo-validador" tabIndex={-1} aria-hidden="true" required value={indiceActual >= 0 && actual !== "" ? actual : ""} onChange={() => undefined} />}
      </div>
      {abierto &&
        createPortal(
          <div
            ref={popRef}
            id={listaId}
            role="listbox"
            className="pop pop-lista"
            data-arriba={pos?.arriba ? "true" : undefined}
            style={pos ? { top: pos.top, left: pos.left, minWidth: pos.minWidth, maxHeight: pos.maxHeight } : { top: 0, left: 0, visibility: "hidden" }}
            // El foco se queda en el campo: pulsar una opción no lo debe quitar
            onMouseDown={(evento) => evento.preventDefault()}
          >
            {opciones.map((opcion, i) => (
              <div
                key={`${opcion.value}-${i}`}
                id={`${listaId}-${i}`}
                role="option"
                aria-selected={i === indiceActual}
                aria-disabled={opcion.disabled || undefined}
                className={`pop-opcion${i === activo ? " activa" : ""}${i === indiceActual ? " elegida" : ""}`}
                onPointerEnter={() => !opcion.disabled && setActivo(i)}
                onClick={() => !opcion.disabled && elegir(i)}
              >
                <span>{opcion.label}</span>
                {i === indiceActual && <CheckIcono />}
              </div>
            ))}
          </div>,
          document.body,
        )}
    </>
  );
}
