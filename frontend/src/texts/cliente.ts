// Textos del portal del cliente, tomados de docs/glosario.md (spec 010, T13).
// Regla: el cliente no ve jerga técnica (principio 8); todo lo que se muestra sale de aquí.
import type { ServiceStatus } from "../api";

export const textosCliente = {
  // Disponibilidad (uptime) frente al objetivo del plan
  disponibilidadDentro: "Su sitio se mantuvo disponible dentro del objetivo acordado.",
  disponibilidadDebajo:
    "Este mes su sitio estuvo disponible menos de lo acordado; le explicamos qué pasó y qué mejoramos.",
  // Sin serie de monitoreo o Prometheus apagado (CA-8)
  sinDatos: "Todavía no tenemos datos de su sitio este mes.",
  // Estado actual del sitio
  sitioOperativo: "Su sitio está disponible.",
  sitioDegradado: "Su sitio funciona, pero más lento o con fallas parciales.",
  sitioCaido: "Su sitio no está disponible en este momento; ya estamos trabajando en ello.",
  // Incidentes del mes y tiempo de recuperación (CA-9)
  sinIncidentes: "No tuvimos fallas que afectaran su sitio este mes.",
  tiempoRecuperacion: "Tiempo que tardamos en recuperar su sitio.",
  fallaCritica: "Falla crítica: atención inmediata.",
  lentitud: "El sitio presentó lentitud y se inició una acción de mejora.",
  // Solicitudes del mes
  solicitud: "Solicitud.",
  sinSolicitudes: "Este mes no abrió solicitudes.",
} as const;

// Estado actual del sitio en palabras del cliente
export function textoEstado(status: ServiceStatus | null | undefined): string {
  if (status === "caido") return textosCliente.sitioCaido;
  if (status === "degradado") return textosCliente.sitioDegradado;
  return textosCliente.sitioOperativo;
}

// Disponibilidad del mes: dentro, por debajo del objetivo o sin datos (nunca un 100 % inventado)
export function textoDisponibilidad(
  availability: number | null | undefined,
  cumpleObjetivo: boolean | null | undefined,
): string {
  if (availability === null || availability === undefined || cumpleObjetivo === null || cumpleObjetivo === undefined) {
    return textosCliente.sinDatos;
  }
  return cumpleObjetivo ? textosCliente.disponibilidadDentro : textosCliente.disponibilidadDebajo;
}

// Tiempo medio de recuperación: sin incidentes reales se dice así, no se muestra 0 (CA-9)
export function textoRecuperacion(mttr: number | null | undefined): string {
  if (mttr === null || mttr === undefined) return textosCliente.sinIncidentes;
  return `${textosCliente.tiempoRecuperacion} ${Math.round(mttr)} min.`;
}
