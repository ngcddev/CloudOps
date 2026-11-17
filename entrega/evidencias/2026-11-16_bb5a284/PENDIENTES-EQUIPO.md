# Pendientes del equipo

> Todo lo que la verificación no puede producir sola. Cada punto es una pregunta concreta. Lo que no se responda queda en el informe como `[COMPLETAR: …]`.

## Datos que solo ustedes tienen

1. **Nombre oficial del proyecto.** En la interfaz la aplicación se llama «CloudOps Client Hub» y la agencia, «Forja Digital». ¿El proyecto se llama CloudForge, CloudOps Client Hub u otro?
2. **Docente, jurado, fecha de entrega y versión del documento.**
3. **Tildes de los nombres:** ¿son correctos Nicolás Gaviria Cerón, Sebastián Camilo Paja Barrios, Andrés Felipe Díaz Duque, Eric Sebastián Mesías Rojas y Yisel Andrea Charo Rivera?
4. **Entrevista con la empresa de software de Sebastián:** nombre de la empresa (o si se anonimiza), fecha, quién respondió, preguntas y respuestas, y permiso para citarla. Sin ella, §4 queda sin el problema concreto del Cauca.
5. **Contexto del Cauca:** ¿qué sector o comunidad representa el caso? (La semilla usa tres pymes de Popayán.)
6. **Objetivos (§4) y partes interesadas (§7):** están propuestos a partir del producto real y llevan `[AUDITAR CON PERPLEXITY]`. Revisarlos y aprobarlos.
7. **Uso de IA en el desarrollo (bitácora 04):** ¿qué fechas, qué tipo de tareas y con qué detalle se declaran los agentes de auditoría con skills en Claude Code? ¿Hay registros (sesiones, PR) que quieran citar?
8. **Riesgos de cronograma (§24):** fechas clave. Ensayo hacia el 21 nov, pruebas el 27 y 28 nov, sustentación el 30 nov: ¿siguen así?

## Decisiones sobre los hallazgos (antes de la entrega)

| Hallazgo | Pregunta | Opciones |
|---|---|---|
| H-IAC-01 (grave): OpenTofu pisa a los clientes reales | ¿Se corrige antes de la entrega? | Importar los tres clientes al estado / sacarlos del inventario / declararlo como límite |
| H-IA-01: la salida del modelo no se redacta | ¿Se corrige? | Agregar la redacción a la respuesta (cambio pequeño en `backend/app/services/assistant.py`) / declararlo |
| H-IA-02: «resume las reglas» filtra el prompt | ¿Se endurece el prompt (v4)? | Endurecer y volver a evaluar / aceptarlo (el prompt es público en el repositorio) |
| H-OPS-02: demo 010 frente a selfHeal | ¿Se reescribe? | Provocar la caída con una versión rota (como `cronometro.sh`) / retirar los pasos 4 a 6 |
| H-TEST-01: 6 pruebas dependen del `.env` | ¿Se fijan? | Fijar el modo en las pruebas / dejar el `.env` en `completo` |
| Rama `dev` sin protección en GitHub | ¿Se protege? | Activar la protección (PR obligatorio) |
| GitHub sin issues (0) ni etiquetas (0) | El entregable 2 pide «issues» | Explicar que la trazabilidad va por specs y PR (213 PR) / crear issues por tarea / crear etiquetas de versión |
| Sin `LICENSE`, `NOTICE` ni `CONTRIBUTING.md` | Apache-2.0 ya decidida | Se agregan en la depuración (fase 2) |
| README sin instrucciones de arranque | — | Se agregan en la depuración (fase 2) |

## Evidencias que faltan (se pueden producir si se decide)

- Captura de una corrida del CI en GitHub Actions y de la puerta en Gitea con su SBOM y firma: hoy solo hay registros de texto (`B/B06`, `C/C23`).
- Guía de acceso al Gitea del laboratorio para el jurado (anexo): pendiente de redactar en la fase 4.
- Despliegue en la nube (GCP o Azure): pendiente por decisión del equipo (D1).
- Ensayo del reinicio completo del clúster: no se hizo, por el riesgo de que el nodo cambie de IP.
