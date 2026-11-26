// Campos de fecha y de mes propios: reemplazan a <input type="date"> y <input type="month">, cuyo calendario nativo no se puede estilizar. Despliegan un calendario en español con la semana desde el lunes; "hoy" se toma en la hora de Bogotá. Avisan el cambio con un evento que trae target.value (AAAA-MM-DD o AAAA-MM), igual que el campo nativo, y respetan min y max.
import { useCallback, useEffect, useId, useMemo, useRef, useState } from "react";
import type { ChangeEvent, KeyboardEvent } from "react";
import { createPortal } from "react-dom";
import { usePopover } from "../hooks/usePopover";
import { CalendarIcon, ChevronRight, ChevronLeft } from "./FieldIcons";
import { changeEvent } from "./Select";

const MONTHS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];
const SHORT_MONTHS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
const DAYS = ["L", "M", "X", "J", "V", "S", "D"];
const LONG_DAYS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"];

interface Day {
  y: number;
  m: number;
  d: number;
}

const pad2 = (n: number) => String(n).padStart(2, "0");
const toText = ({ y, m, d }: Day) => `${y}-${pad2(m)}-${pad2(d)}`;
const toMonthText = (y: number, m: number) => `${y}-${pad2(m)}`;

function parseDate(texto: string): Day | null {
  const c = /^(\d{4})-(\d{2})-(\d{2})$/.exec(texto);
  return c ? { y: Number(c[1]), m: Number(c[2]), d: Number(c[3]) } : null;
}

function parseMonth(texto: string): { y: number; m: number } | null {
  const c = /^(\d{4})-(\d{2})$/.exec(texto);
  return c ? { y: Number(c[1]), m: Number(c[2]) } : null;
}

function addDays(base: Day, dias: number): Day {
  const f = new Date(Date.UTC(base.y, base.m - 1, base.d + dias));
  return { y: f.getUTCFullYear(), m: f.getUTCMonth() + 1, d: f.getUTCDate() };
}

// Mantiene el día y lo recorta al último del mes de llegada (31 de enero + 1 mes = 28 o 29 de febrero)
function addMonths(base: Day, meses: number): Day {
  const total = base.y * 12 + (base.m - 1) + meses;
  const y = Math.floor(total / 12);
  const m = (total % 12) + 1;
  const ultimo = new Date(Date.UTC(y, m, 0)).getUTCDate();
  return { y, m, d: Math.min(base.d, ultimo) };
}

// Lunes = 0 … domingo = 6
const weekday = (f: Day) => (new Date(Date.UTC(f.y, f.m - 1, f.d)).getUTCDay() + 6) % 7;

// Hoy en la hora de Bogotá, no en la del navegador
function todayInBogota(): Day {
  const texto = new Intl.DateTimeFormat("en-CA", { timeZone: "America/Bogota" }).format(new Date());
  return parseDate(texto) ?? { y: 1970, m: 1, d: 1 };
}

const capitalize = (texto: string) => texto.charAt(0).toUpperCase() + texto.slice(1);
const dateText = (valor: string) => {
  const f = parseDate(valor);
  return f ? `${f.d} ${SHORT_MONTHS[f.m - 1]} ${f.y}` : "";
};
const monthText = (valor: string) => {
  const f = parseMonth(valor);
  return f ? `${capitalize(MONTHS[f.m - 1])} de ${f.y}` : "";
};

export interface DateFieldProps {
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

interface CalendarProps {
  valor: string;
  min?: string;
  max?: string;
  puedeBorrar: boolean;
  onElegir: (fecha: Day | null) => void;
  onCerrar: () => void;
}

function DayCalendar({ valor, min, max, puedeBorrar, onElegir, onCerrar }: CalendarProps) {
  const hoy = useMemo(todayInBogota, []);
  const enRango = useCallback((f: Day) => {
    const t = toText(f);
    return (!min || t >= min) && (!max || t <= max);
  }, [min, max]);
  // Si el rango deja fuera a un día, el foco cae en el límite más cercano
  const ajustar = useCallback(
    (f: Day): Day => {
      const t = toText(f);
      if (max && t > max) return parseDate(max) ?? f;
      if (min && t < min) return parseDate(min) ?? f;
      return f;
    },
    [min, max],
  );
  const [foco, setFoco] = useState<Day>(() => ajustar(parseDate(valor) ?? hoy));
  const cuadriculaRef = useRef<HTMLDivElement>(null);
  const primera = useRef(true);

  // Al abrir, el foco entra al día elegido (o a hoy); después sigue a las flechas sin robárselo a los botones de navegación
  useEffect(() => {
    const boton = cuadriculaRef.current?.querySelector<HTMLButtonElement>('button[tabindex="0"]');
    const activo = document.activeElement;
    if (boton && (primera.current || !activo || activo === document.body || cuadriculaRef.current?.contains(activo))) boton.focus();
    primera.current = false;
  }, [foco]);

  const primeroDelMes: Day = { y: foco.y, m: foco.m, d: 1 };
  const celdas = Array.from({ length: 42 }, (_, i) => addDays(primeroDelMes, i - weekday(primeroDelMes)));
  const textoHoy = toText(hoy);

  const alTeclear = (evento: KeyboardEvent<HTMLDivElement>) => {
    if (evento.key === "Escape") {
      evento.preventDefault();
      evento.stopPropagation();
      onCerrar();
      return;
    }
    if (!(evento.target as HTMLElement).closest(".cal-cuadricula")) return;
    let siguiente: Day | null = null;
    switch (evento.key) {
      case "ArrowLeft": siguiente = addDays(foco, -1); break;
      case "ArrowRight": siguiente = addDays(foco, 1); break;
      case "ArrowUp": siguiente = addDays(foco, -7); break;
      case "ArrowDown": siguiente = addDays(foco, 7); break;
      case "Home": siguiente = addDays(foco, -weekday(foco)); break;
      case "End": siguiente = addDays(foco, 6 - weekday(foco)); break;
      case "PageUp": siguiente = addMonths(foco, evento.shiftKey ? -12 : -1); break;
      case "PageDown": siguiente = addMonths(foco, evento.shiftKey ? 12 : 1); break;
    }
    if (siguiente) {
      evento.preventDefault();
      setFoco(ajustar(siguiente));
    }
  };

  return (
    <div onKeyDown={alTeclear}>
      <div className="cal-cabecera">
        <button type="button" className="cal-nav" aria-label="Mes anterior" onClick={() => setFoco(ajustar(addMonths(foco, -1)))}>
          <ChevronLeft />
        </button>
        <div className="cal-titulo" aria-live="polite">
          {capitalize(MONTHS[foco.m - 1])} de {foco.y}
        </div>
        <button type="button" className="cal-nav" aria-label="Mes siguiente" onClick={() => setFoco(ajustar(addMonths(foco, 1)))}>
          <ChevronRight />
        </button>
      </div>
      <div className="cal-cuadricula" role="group" aria-label={`${capitalize(MONTHS[foco.m - 1])} de ${foco.y}`} ref={cuadriculaRef}>
        {DAYS.map((letra, i) => (
          <div key={letra} className="cal-dia-nombre" aria-label={LONG_DAYS[i]}>
            {letra}
          </div>
        ))}
        {celdas.map((f) => {
          const texto = toText(f);
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
              aria-label={`${LONG_DAYS[weekday(f)]} ${f.d} de ${MONTHS[f.m - 1]} de ${f.y}${esHoy ? ", hoy" : ""}`}
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

interface MonthsProps {
  valor: string;
  min?: string;
  max?: string;
  onElegir: (anio: number, mes: number) => void;
  onCerrar: () => void;
}

function MonthCalendar({ valor, min, max, onElegir, onCerrar }: MonthsProps) {
  const hoy = useMemo(todayInBogota, []);
  const enRango = useCallback(
    (y: number, m: number) => {
      const t = toMonthText(y, m);
      return (!min || t >= min) && (!max || t <= max);
    },
    [min, max],
  );
  const ajustar = useCallback(
    (y: number, m: number) => {
      const t = toMonthText(y, m);
      if (max && t > max) return parseMonth(max) ?? { y, m };
      if (min && t < min) return parseMonth(min) ?? { y, m };
      return { y, m };
    },
    [min, max],
  );
  const [foco, setFoco] = useState(() => {
    const inicial = parseMonth(valor) ?? { y: hoy.y, m: hoy.m };
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

  const textoActual = toMonthText(hoy.y, hoy.m);
  return (
    <div onKeyDown={alTeclear}>
      <div className="cal-cabecera">
        <button type="button" className="cal-nav" aria-label="Año anterior" onClick={() => mover(-12)}>
          <ChevronLeft />
        </button>
        <div className="cal-titulo" aria-live="polite">
          {foco.y}
        </div>
        <button type="button" className="cal-nav" aria-label="Año siguiente" onClick={() => mover(12)}>
          <ChevronRight />
        </button>
      </div>
      <div className="cal-meses" role="group" aria-label={`Meses de ${foco.y}`} ref={cuadriculaRef}>
        {MONTHS.map((nombre, i) => {
          const texto = toMonthText(foco.y, i + 1);
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
              {SHORT_MONTHS[i]}
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

interface FieldBaseProps extends DateFieldProps {
  texto: string;
  tituloDialogo: string;
  altoMaximo: number;
  contenido: (cerrarYElegir: (valor: string) => void, cerrar: () => void) => JSX.Element;
  claseLista: string;
}

function FieldBase({ value, onChange, id, name, disabled, required, className, placeholder, texto, tituloDialogo, altoMaximo, contenido, claseLista, ...resto }: FieldBaseProps) {
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
    if (nuevo !== value) onChange(changeEvent<HTMLInputElement>(nuevo, name));
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
          <CalendarIcon />
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

export function DateField({ value, min, max, required, placeholder = "Seleccionar fecha", ...resto }: DateFieldProps) {
  return (
    <FieldBase
      {...resto}
      value={value}
      min={min}
      max={max}
      required={required}
      placeholder={placeholder}
      texto={dateText(value)}
      tituloDialogo="Elegir fecha"
      altoMaximo={460}
      claseLista="pop-calendario"
      contenido={(elegir, cerrar) => (
        <DayCalendar valor={value} min={min} max={max} puedeBorrar={!required} onElegir={(f) => elegir(f ? toText(f) : "")} onCerrar={cerrar} />
      )}
    />
  );
}

export function MonthField({ value, min, max, required, placeholder = "Seleccionar mes", ...resto }: DateFieldProps) {
  return (
    <FieldBase
      {...resto}
      value={value}
      min={min}
      max={max}
      required={required}
      placeholder={placeholder}
      texto={monthText(value)}
      tituloDialogo="Elegir mes"
      altoMaximo={380}
      claseLista="pop-meses"
      contenido={(elegir, cerrar) => <MonthCalendar valor={value} min={min} max={max} onElegir={(y, m) => elegir(toMonthText(y, m))} onCerrar={cerrar} />}
    />
  );
}
