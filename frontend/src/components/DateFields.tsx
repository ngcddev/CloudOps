// Campos de fecha y de mes propios: reemplazan a <input type="date"> y <input type="month">, cuyo calendario nativo no se puede estilizar. Despliegan un calendario en español con la semana desde el lunes; "hoy" se toma en la hora de Bogotá. Avisan el cambio con un evento que trae target.value (AAAA-MM-DD o AAAA-MM), igual que el campo nativo, y respetan min y max.
import { useCallback, useEffect, useId, useMemo, useRef, useState } from "react";
import type { ChangeEvent, KeyboardEvent } from "react";
import { createPortal } from "react-dom";
import { usePopover } from "../hooks/usePopover";
import { CalendarioIcono, ChevronDerecha, ChevronIzquierda } from "./IconosCampo";
import { eventoDeCambio } from "./Select";

const MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];
const MESES_CORTOS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
const DIAS = ["L", "M", "X", "J", "V", "S", "D"];
const DIAS_LARGOS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"];

interface Dia {
  y: number;
  m: number;
  d: number;
}

const dos = (n: number) => String(n).padStart(2, "0");
const aTexto = ({ y, m, d }: Dia) => `${y}-${dos(m)}-${dos(d)}`;
const aTextoMes = (y: number, m: number) => `${y}-${dos(m)}`;

function leerFecha(texto: string): Dia | null {
  const c = /^(\d{4})-(\d{2})-(\d{2})$/.exec(texto);
  return c ? { y: Number(c[1]), m: Number(c[2]), d: Number(c[3]) } : null;
}

function leerMes(texto: string): { y: number; m: number } | null {
  const c = /^(\d{4})-(\d{2})$/.exec(texto);
  return c ? { y: Number(c[1]), m: Number(c[2]) } : null;
}

function sumarDias(base: Dia, dias: number): Dia {
  const f = new Date(Date.UTC(base.y, base.m - 1, base.d + dias));
  return { y: f.getUTCFullYear(), m: f.getUTCMonth() + 1, d: f.getUTCDate() };
}

// Mantiene el día y lo recorta al último del mes de llegada (31 de enero + 1 mes = 28 o 29 de febrero)
function sumarMeses(base: Dia, meses: number): Dia {
  const total = base.y * 12 + (base.m - 1) + meses;
  const y = Math.floor(total / 12);
  const m = (total % 12) + 1;
  const ultimo = new Date(Date.UTC(y, m, 0)).getUTCDate();
  return { y, m, d: Math.min(base.d, ultimo) };
}

// Lunes = 0 … domingo = 6
const diaDeSemana = (f: Dia) => (new Date(Date.UTC(f.y, f.m - 1, f.d)).getUTCDay() + 6) % 7;

// Hoy en la hora de Bogotá, no en la del navegador
function hoyEnBogota(): Dia {
  const texto = new Intl.DateTimeFormat("en-CA", { timeZone: "America/Bogota" }).format(new Date());
  return leerFecha(texto) ?? { y: 1970, m: 1, d: 1 };
}

const mayuscula = (texto: string) => texto.charAt(0).toUpperCase() + texto.slice(1);
const textoFecha = (valor: string) => {
  const f = leerFecha(valor);
  return f ? `${f.d} ${MESES_CORTOS[f.m - 1]} ${f.y}` : "";
};
const textoMes = (valor: string) => {
  const f = leerMes(valor);
  return f ? `${mayuscula(MESES[f.m - 1])} de ${f.y}` : "";
};

export interface CampoFechaProps {
  value: string;
  onChange: (evento: ChangeEvent<HTMLInputElement>) => void;
  min?: string;
  max?: string;
  id?: string;
  name?: string;
  disabled?: boolean;
  required?: boolean;
  placeholder?: string;
  className?: string;
  "aria-label"?: string;
  "aria-labelledby"?: string;
  "aria-invalid"?: boolean | "true" | "false";
  "aria-describedby"?: string;
}

// ---------- Calendario de días ----------

interface CalendarioProps {
  valor: string;
  min?: string;
  max?: string;
  puedeBorrar: boolean;
  onElegir: (fecha: Dia | null) => void;
  onCerrar: () => void;
}

function CalendarioDias({ valor, min, max, puedeBorrar, onElegir, onCerrar }: CalendarioProps) {
  const hoy = useMemo(hoyEnBogota, []);
  const enRango = useCallback((f: Dia) => {
    const t = aTexto(f);
    return (!min || t >= min) && (!max || t <= max);
  }, [min, max]);
  // Si el rango deja fuera a un día, el foco cae en el límite más cercano
  const ajustar = useCallback(
    (f: Dia): Dia => {
      const t = aTexto(f);
      if (max && t > max) return leerFecha(max) ?? f;
      if (min && t < min) return leerFecha(min) ?? f;
      return f;
    },
    [min, max],
  );
  const [foco, setFoco] = useState<Dia>(() => ajustar(leerFecha(valor) ?? hoy));
  const cuadriculaRef = useRef<HTMLDivElement>(null);
  const primera = useRef(true);

  // Al abrir, el foco entra al día elegido (o a hoy); después sigue a las flechas sin robárselo a los botones de navegación
  useEffect(() => {
    const boton = cuadriculaRef.current?.querySelector<HTMLButtonElement>('button[tabindex="0"]');
    const activo = document.activeElement;
    if (boton && (primera.current || !activo || activo === document.body || cuadriculaRef.current?.contains(activo))) boton.focus();
    primera.current = false;
  }, [foco]);

  const primeroDelMes: Dia = { y: foco.y, m: foco.m, d: 1 };
  const celdas = Array.from({ length: 42 }, (_, i) => sumarDias(primeroDelMes, i - diaDeSemana(primeroDelMes)));
  const textoHoy = aTexto(hoy);

  const alTeclear = (evento: KeyboardEvent<HTMLDivElement>) => {
    if (evento.key === "Escape") {
      evento.preventDefault();
      evento.stopPropagation();
      onCerrar();
      return;
    }
    if (!(evento.target as HTMLElement).closest(".cal-cuadricula")) return;
    let siguiente: Dia | null = null;
    switch (evento.key) {
      case "ArrowLeft": siguiente = sumarDias(foco, -1); break;
      case "ArrowRight": siguiente = sumarDias(foco, 1); break;
      case "ArrowUp": siguiente = sumarDias(foco, -7); break;
      case "ArrowDown": siguiente = sumarDias(foco, 7); break;
      case "Home": siguiente = sumarDias(foco, -diaDeSemana(foco)); break;
      case "End": siguiente = sumarDias(foco, 6 - diaDeSemana(foco)); break;
      case "PageUp": siguiente = sumarMeses(foco, evento.shiftKey ? -12 : -1); break;
      case "PageDown": siguiente = sumarMeses(foco, evento.shiftKey ? 12 : 1); break;
    }
    if (siguiente) {
      evento.preventDefault();
      setFoco(ajustar(siguiente));
    }
  };

  return (
    <div onKeyDown={alTeclear}>
      <div className="cal-cabecera">
        <button type="button" className="cal-nav" aria-label="Mes anterior" onClick={() => setFoco(ajustar(sumarMeses(foco, -1)))}>
          <ChevronIzquierda />
        </button>
        <div className="cal-titulo" aria-live="polite">
          {mayuscula(MESES[foco.m - 1])} de {foco.y}
        </div>
        <button type="button" className="cal-nav" aria-label="Mes siguiente" onClick={() => setFoco(ajustar(sumarMeses(foco, 1)))}>
          <ChevronDerecha />
        </button>
      </div>
      <div className="cal-cuadricula" role="group" aria-label={`${mayuscula(MESES[foco.m - 1])} de ${foco.y}`} ref={cuadriculaRef}>
        {DIAS.map((letra, i) => (
          <div key={letra} className="cal-dia-nombre" aria-label={DIAS_LARGOS[i]}>
            {letra}
          </div>
        ))}
        {celdas.map((f) => {
          const texto = aTexto(f);
          const esFoco = f.y === foco.y && f.m === foco.m && f.d === foco.d;
          const esHoy = texto === textoHoy;
          return (
            <button
              key={texto}
              type="button"
              tabIndex={esFoco ? 0 : -1}
              className={`cal-dia${f.m !== foco.m ? " fuera" : ""}${esHoy ? " hoy" : ""}`}
              aria-pressed={texto === valor}
              aria-current={esHoy ? "date" : undefined}
              aria-label={`${DIAS_LARGOS[diaDeSemana(f)]} ${f.d} de ${MESES[f.m - 1]} de ${f.y}${esHoy ? ", hoy" : ""}`}
              disabled={!enRango(f)}
              onClick={() => onElegir(f)}
            >
              {f.d}
            </button>
          );
        })}
      </div>
      <div className="cal-pie">
        <button type="button" className="cal-accion" disabled={!enRango(hoy)} onClick={() => onElegir(hoy)}>
          Hoy
        </button>
        {puedeBorrar && valor && (
          <button type="button" className="cal-accion" onClick={() => onElegir(null)}>
            Borrar
          </button>
        )}
      </div>
    </div>
  );
}

// ---------- Calendario de meses ----------

interface MesesProps {
  valor: string;
  min?: string;
  max?: string;
  onElegir: (anio: number, mes: number) => void;
  onCerrar: () => void;
}

function CalendarioMeses({ valor, min, max, onElegir, onCerrar }: MesesProps) {
  const hoy = useMemo(hoyEnBogota, []);
  const enRango = useCallback(
    (y: number, m: number) => {
      const t = aTextoMes(y, m);
      return (!min || t >= min) && (!max || t <= max);
    },
    [min, max],
  );
  const ajustar = useCallback(
    (y: number, m: number) => {
      const t = aTextoMes(y, m);
      if (max && t > max) return leerMes(max) ?? { y, m };
      if (min && t < min) return leerMes(min) ?? { y, m };
      return { y, m };
    },
    [min, max],
  );
  const [foco, setFoco] = useState(() => {
    const inicial = leerMes(valor) ?? { y: hoy.y, m: hoy.m };
    return ajustar(inicial.y, inicial.m);
  });
  const cuadriculaRef = useRef<HTMLDivElement>(null);
  const primera = useRef(true);

  useEffect(() => {
    const boton = cuadriculaRef.current?.querySelector<HTMLButtonElement>('button[tabindex="0"]');
    const activo = document.activeElement;
    if (boton && (primera.current || !activo || activo === document.body || cuadriculaRef.current?.contains(activo))) boton.focus();
    primera.current = false;
  }, [foco]);

  const mover = (meses: number) => {
    const total = foco.y * 12 + (foco.m - 1) + meses;
    setFoco(ajustar(Math.floor(total / 12), (total % 12) + 1));
  };

  const alTeclear = (evento: KeyboardEvent<HTMLDivElement>) => {
    if (evento.key === "Escape") {
      evento.preventDefault();
      evento.stopPropagation();
      onCerrar();
      return;
    }
    if (!(evento.target as HTMLElement).closest(".cal-meses")) return;
    const cambios: Record<string, number> = { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -3, ArrowDown: 3, PageUp: -12, PageDown: 12, Home: 1 - foco.m, End: 12 - foco.m };
    if (evento.key in cambios) {
      evento.preventDefault();
      mover(cambios[evento.key]);
    }
  };

  const textoActual = aTextoMes(hoy.y, hoy.m);
  return (
    <div onKeyDown={alTeclear}>
      <div className="cal-cabecera">
        <button type="button" className="cal-nav" aria-label="Año anterior" onClick={() => mover(-12)}>
          <ChevronIzquierda />
        </button>
        <div className="cal-titulo" aria-live="polite">
          {foco.y}
        </div>
        <button type="button" className="cal-nav" aria-label="Año siguiente" onClick={() => mover(12)}>
          <ChevronDerecha />
        </button>
      </div>
      <div className="cal-meses" role="group" aria-label={`Meses de ${foco.y}`} ref={cuadriculaRef}>
        {MESES.map((nombre, i) => {
          const texto = aTextoMes(foco.y, i + 1);
          const esActual = texto === textoActual;
          return (
            <button
              key={nombre}
              type="button"
              tabIndex={foco.m === i + 1 ? 0 : -1}
              className={`cal-mes${esActual ? " hoy" : ""}`}
              aria-pressed={texto === valor}
              aria-current={esActual ? "date" : undefined}
              aria-label={`${nombre} de ${foco.y}${esActual ? ", este mes" : ""}`}
              disabled={!enRango(foco.y, i + 1)}
              onClick={() => onElegir(foco.y, i + 1)}
            >
              {MESES_CORTOS[i]}
            </button>
          );
        })}
      </div>
      <div className="cal-pie">
        <button type="button" className="cal-accion" disabled={!enRango(hoy.y, hoy.m)} onClick={() => onElegir(hoy.y, hoy.m)}>
          Este mes
        </button>
      </div>
    </div>
  );
}

// ---------- Campos ----------

interface CampoBaseProps extends CampoFechaProps {
  texto: string;
  tituloDialogo: string;
  altoMaximo: number;
  contenido: (cerrarYElegir: (valor: string) => void, cerrar: () => void) => JSX.Element;
  claseLista: string;
}

function CampoBase({ value, onChange, id, name, disabled, required, className, placeholder, texto, tituloDialogo, altoMaximo, contenido, claseLista, ...resto }: CampoBaseProps) {
  const aria = {
    "aria-label": resto["aria-label"],
    "aria-labelledby": resto["aria-labelledby"],
    "aria-invalid": resto["aria-invalid"],
    "aria-describedby": resto["aria-describedby"],
  };
  const [abierto, setAbierto] = useState(false);
  const cerrar = useCallback(() => setAbierto(false), []);
  const { triggerRef, popRef, pos } = usePopover(abierto, cerrar, altoMaximo);
  const dialogoId = useId();

  const cerrarConFoco = () => {
    setAbierto(false);
    triggerRef.current?.focus();
  };
  const elegir = (nuevo: string) => {
    cerrarConFoco();
    if (nuevo !== value) onChange(eventoDeCambio<HTMLInputElement>(nuevo, name));
  };

  return (
    <>
      <div className="campo-envoltura">
        <button
          type="button"
          ref={triggerRef}
          id={id}
          className={`campo-disparador${className ? ` ${className}` : ""}`}
          aria-haspopup="dialog"
          aria-expanded={abierto}
          aria-required={required || undefined}
          aria-controls={abierto ? dialogoId : undefined}
          disabled={disabled}
          onClick={() => setAbierto((estaba) => !estaba)}
          onKeyDown={(evento) => {
            // Con el foco en el campo: Esc cierra el calendario y la flecha abajo lo abre
            if (evento.key === "Escape" && abierto) {
              evento.preventDefault();
              evento.stopPropagation();
              cerrar();
            } else if (evento.key === "ArrowDown" && !abierto && !disabled) {
              evento.preventDefault();
              setAbierto(true);
            }
          }}
          {...aria}
        >
          <span className={`campo-valor${value ? "" : " campo-vacio"}`}>{value ? texto : placeholder}</span>
          <CalendarioIcono />
        </button>
        {/* Un botón no se valida solo: este campo oculto hace que "obligatorio" siga frenando el envío del formulario */}
        {required && <input className="campo-validador" tabIndex={-1} aria-hidden="true" required value={value} onChange={() => undefined} />}
      </div>
      {abierto &&
        createPortal(
          <div
            ref={popRef}
            id={dialogoId}
            role="dialog"
            aria-label={tituloDialogo}
            className={`pop ${claseLista}`}
            data-arriba={pos?.arriba ? "true" : undefined}
            style={pos ? { top: pos.top, left: pos.left, maxHeight: pos.maxHeight } : { top: 0, left: 0, visibility: "hidden" }}
          >
            {contenido(elegir, cerrarConFoco)}
          </div>,
          document.body,
        )}
    </>
  );
}

export function DateField({ value, min, max, required, placeholder = "Seleccionar fecha", ...resto }: CampoFechaProps) {
  return (
    <CampoBase
      {...resto}
      value={value}
      min={min}
      max={max}
      required={required}
      placeholder={placeholder}
      texto={textoFecha(value)}
      tituloDialogo="Elegir fecha"
      altoMaximo={460}
      claseLista="pop-calendario"
      contenido={(elegir, cerrar) => (
        <CalendarioDias valor={value} min={min} max={max} puedeBorrar={!required} onElegir={(f) => elegir(f ? aTexto(f) : "")} onCerrar={cerrar} />
      )}
    />
  );
}

export function MonthField({ value, min, max, required, placeholder = "Seleccionar mes", ...resto }: CampoFechaProps) {
  return (
    <CampoBase
      {...resto}
      value={value}
      min={min}
      max={max}
      required={required}
      placeholder={placeholder}
      texto={textoMes(value)}
      tituloDialogo="Elegir mes"
      altoMaximo={380}
      claseLista="pop-meses"
      contenido={(elegir, cerrar) => <CalendarioMeses valor={value} min={min} max={max} onElegir={(y, m) => elegir(aTextoMes(y, m))} onCerrar={cerrar} />}
    />
  );
}
