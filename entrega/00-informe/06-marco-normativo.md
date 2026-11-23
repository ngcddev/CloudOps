<!-- Sección 6 · Fuente: normas y políticas citadas; controles tomados del código y de los ADR. Verificación de fuentes el 16 nov 2026: CONPES 4144 (DNP, 14 feb 2025), SLSA v1.2 (slsa.dev, nov 2025), NIST SP 800-218 v1.1 (feb 2022), MinTIC Res. 500/2021 y 746/2022, ISO/IEC 25010:2023 (edición 2, nov 2023: nueve características). -->
<!-- Citas para la sección Referencias (APA): Congreso de la República de Colombia (2012); DNP (2025); MinTIC (2021, 2022); NIST (2022, 2024); SLSA (2025); ISO/IEC (2022); ISO/IEC (2023a) = 42001; ISO/IEC (2023b) = 25010. -->
<!-- Numeración de controles de ISO/IEC 27001:2022 Anexo A: contrastar con el texto de la norma antes de entregar. -->

# Marco normativo

El proyecto no certifica ninguna norma. Las normas y políticas que siguen son el marco de referencia con el que se diseñaron los controles; en cada caso el informe dice cómo afecta al proyecto y dónde está el control, y usa la expresión «alineado con» y nunca «cumple» ni «certificado». Las normas de gestión (ISO/IEC 27001 y 42001) piden un sistema de gestión de una organización, que un proyecto académico no tiene; aquí se usan como catálogo de controles.

::: {custom-style="Table Caption"}
**Tabla {T:normas}**\
*Marco normativo y su efecto en el proyecto*
:::

| Norma o política | Qué establece | Cómo afecta al proyecto | Control y evidencia |
|---------------|----------------------|----------------------------|-----------------------|
| Ley 1581 de 2012 (Congreso de la República de Colombia, 2012) | Régimen general de protección de datos personales (habeas data): principios de finalidad, veracidad, transparencia, seguridad y confidencialidad, y derechos del titular | El Hub guarda nombres, correos y teléfonos de contacto y direcciones IP; por eso se minimizan los datos, se protegen las credenciales y los datos no salen del laboratorio | Datos sintéticos; bcrypt, roles y alcance por cliente; redacción de secretos; sin IA externa (RNF-09, RNF-18; sección de modelo de datos) |
| CONPES 4144 de 2025 (Departamento Nacional de Planeación [DNP], 2025) | Política Nacional de Inteligencia Artificial, aprobada el 14 de febrero de 2025: capacidades para investigar, desarrollar, adoptar y aprovechar la IA de forma ética y sostenible, con ejes de ética y gobernanza y de datos e infraestructura | La IA del proyecto es local, transparente y con una persona que decide: nada llega al cliente sin aprobación y cada respuesta cita sus fuentes | Compuerta y RAG con fuentes; borradores aprobados; fichas de modelos con licencia, límites y riesgos (RF-18, RF-25, RF-28; sección de validación de IA) |
| Lineamientos de seguridad y privacidad de MinTIC (Ministerio de Tecnologías de la Información y las Comunicaciones [MinTIC], 2021, 2022) | Modelo de Seguridad y Privacidad de la Información (MSPI), adoptado por la Resolución 500 de 2021 y modificada por la Resolución 746 de 2022, para las entidades públicas, con cinco fases y el objetivo de preservar la confidencialidad, la integridad y la disponibilidad | Es obligatorio para entidades públicas, no para este proyecto; se toma como guía de ciclo: planificar, implementar, evaluar y mejorar | Modelo de amenazas, riesgos y auditoría del proyecto (`docs/modelo-de-amenazas.md`, `docs/auditoria-2026-11.md`) |
| NIST SP 800-218, SSDF v1.1 (National Institute of Standards and Technology [NIST], 2022) | Prácticas de desarrollo seguro de software agrupadas en preparar la organización, proteger el software, producir software bien protegido y responder a vulnerabilidades | La puerta de seguridad y la CI aplican esas prácticas: análisis de secretos, análisis estático, de dependencias y de imagen, SBOM y registro de hallazgos con decisión y vencimiento. Existe además un perfil para IA generativa (SP 800-218A; NIST, 2024) | `pipelines/puerta.yaml`, `.github/workflows/ci.yml`, `pipelines/hallazgos.yaml` (RF-08, RNF-05, RNF-06) |
| SLSA v1.2 (SLSA, 2025) | Niveles de garantía de la cadena de suministro; la versión 1.2 de noviembre de 2025 agrega el seguimiento del código fuente y mantiene la compatibilidad con la 1.1 | Cada imagen que pasa la puerta se firma y lleva una atestación de procedencia verificada; no se declara un nivel de SLSA | Atestación `slsaprovenance1` firmada y verificada con Cosign (`pipelines/puerta.sh:213-265`, ADR-09) |
| ISO/IEC 27001:2022 (ISO/IEC, 2022) | Requisitos de un sistema de gestión de seguridad de la información y controles del Anexo A | Se usa como catálogo de controles: registro de eventos, respaldos, control de acceso, ciclo de desarrollo seguro y gestión de cambios | Bitácora de auditoría, respaldo diario, roles, puerta de seguridad y segregación de funciones (ADR-03, ADR-11; secciones de pipeline y de datos) |
| ISO/IEC 42001:2023 (ISO/IEC, 2023a) | Requisitos de un sistema de gestión de inteligencia artificial: gobierno, evaluación de riesgos e impactos, transparencia y supervisión humana | Se usa como guía para documentar y controlar la IA: fichas de modelos, análisis de riesgos de IA, evaluación y supervisión humana | `docs/modelos/`, evaluación en `ai/eval/`, aprobación humana (secciones de MLOps y de validación de IA) |
| ISO/IEC 25010:2023 (ISO/IEC, 2023b) | Modelo de calidad del producto, edición 2 de noviembre de 2023, con nueve características | Ordena los requerimientos no funcionales y sus métricas | Sección de requerimientos no funcionales (Tabla {T:rnf}) |

::: {custom-style="Nota"}
*Nota.* Elaboración propia. Las referencias completas están en la sección Referencias. La Resolución 500 de 2021 y la 746 de 2022 se citan por su contenido general; el equipo debe confirmar con el sitio de Gobierno Digital de MinTIC qué versión del documento maestro está vigente al entregar.
:::

## Efecto de la normativa en las decisiones de diseño

- **Protección de datos personales.** Todos los datos del laboratorio son sintéticos y ningún dato sale a una IA externa (RNF-09). Si el Hub pasara a datos reales, la agencia sería responsable o encargada del tratamiento de los contactos de sus clientes y tendría que contar con autorización de los titulares, una política de tratamiento y una política de retención; hoy la retención de las preguntas al asistente y de los textos libres no está definida (sección de modelo de datos).
- **IA responsable.** El modelo no decide ni ejecuta: explica, redacta borradores y cita sus fuentes; la aprobación es humana y queda en la bitácora. Los riesgos, las licencias y los límites de cada modelo están documentados.
- **Cadena de suministro.** Cada versión de un sitio pasa por controles antes de publicarse, queda con inventario de componentes (SBOM) y procedencia firmada, y las vulnerabilidades sin arreglo tienen una decisión con fecha de revisión.
- **Calidad.** Los requerimientos no funcionales siguen las características de ISO/IEC 25010:2023 y cada uno tiene una métrica verificable.

## Normas que no se aplican

No se aplican normas sectoriales (por ejemplo, de datos de salud o financieros) porque el proyecto no procesa esos datos, y no se evalúa ninguna certificación de organización, por ser un proyecto académico. Los clientes de ejemplo incluyen un consultorio dental: si se usaran datos reales de pacientes, esos datos serían datos sensibles de salud y exigirían un tratamiento reforzado que este proyecto no implementa.
