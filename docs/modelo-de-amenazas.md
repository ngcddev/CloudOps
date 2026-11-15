# Modelo de amenazas del Hub (spec 018, T07)

Una página: qué hay que proteger, quién podría atacar, por dónde, y qué lo frena hoy. Se revisa cuando entra un componente nuevo o cada seis meses
(próxima revisión: **2027-05-15**). Las decisiones sobre vulnerabilidades concretas están en [`pipelines/hallazgos.yaml`](../pipelines/hallazgos.yaml).

## Activos

| Activo | Por qué importa |
|---|---|
| Datos de clientes (solicitudes, incidentes, citas, mensajes) | Son del cliente; ninguno sale del laboratorio (principio 2) |
| Sesiones y roles (agencia / cliente) | Quien tenga una sesión de agencia puede pedir y aprobar cambios |
| Repositorio `hub-gitops` en Gitea | Lo que está ahí es lo que Argo CD publica en los sitios |
| Clave de firma de Cosign | Decide qué imagen se considera de confianza |
| Tokens de integración (Gitea, Argo CD, pipeline, Alertmanager) | Cada uno abre una puerta del Hub hacia otra herramienta |
| Imágenes de los sitios y del Hub | Se ejecutan dentro del clúster |
| Bitácora de auditoría | Es la prueba de quién hizo qué |

## Fronteras de confianza

Navegador → Ingress (Traefik) → Hub (web y API) → {PostgreSQL, Gitea, Argo CD, Prometheus, Ollama}. Aparte: runner de Gitea Actions → registro de
imágenes → Argo CD → namespaces de clientes. Las fronteras que más pesan son **cliente ↔ agencia** (roles del Hub) y **Hub ↔ clúster** (el Hub no habla
con Kubernetes: solo con Gitea, Argo CD y Prometheus).

## Amenazas y controles

| # | Amenaza | Control que existe | Riesgo que queda |
|---|---|---|---|
| 1 | Un cliente ve datos de otro cliente | Cada ruta filtra por el cliente de la sesión; pruebas de acceso entre clientes (`test_acceso_*`) | Un fallo nuevo de filtrado: se cubre solo con pruebas por ruta nueva |
| 2 | Sesión robada o suplantada | Token firmado con clave propia, contraseñas con bcrypt, expiración de la sesión | En el laboratorio el Hub se sirve por HTTP; en producción exige HTTPS |
| 3 | Una persona se aprueba su propio cambio | Segregación de funciones: quien pide un cambio no lo aprueba (403, queda en bitácora); aprobar exige otra cuenta de la agencia | Dos cuentas de la agencia que se prestan la clave |
| 4 | Se publica una imagen con un secreto, una CVE crítica o una dependencia vulnerable | Puerta de seguridad: Gitleaks, pruebas, Trivy (imagen, dependencias y configuración), licencias; el Hub no deja aprobar una versión que no pasó | Vulnerabilidades sin arreglo: se aceptan con razón y fecha en el registro de hallazgos |
| 5 | Se sustituye una imagen por otra manipulada | Firma con Cosign, procedencia SLSA y SBOM firmado, verificados por la puerta; política de admisión que solo deja registro y etiqueta permitidos | La clave de firma vive en un secreto de Gitea; sin transparencia pública (laboratorio) |
| 6 | Alguien despliega a mano o cambia algo fuera de Git | Argo CD con `selfHeal` revierte el cambio; AppProject `clientes` limita qué puede crear | Quien tenga acceso de administrador al clúster |
| 7 | Un sitio comprometido se mueve hacia otros | Pod Security `restricted`, sin root, sin capacidades, sistema de archivos de solo lectura, sin token de la API montado, NetworkPolicy de denegación por defecto | La plataforma aún escribe en disco (excepción KSV-0014, vence 2027-03-31) |
| 8 | Se filtra un token de integración | Tokens por separado y con el mínimo permiso (Argo CD de solo lectura), en `.env` y Secrets, nunca en el repositorio; Gitleaks en cada cambio | Un token filtrado sigue sirviendo hasta que se rota; no hay rotación automática |
| 9 | Se manipula la bitácora o se niega una acción | Cada acción sensible deja un registro con persona, hora y dirección; los intentos denegados también | Quien tenga acceso a la base de datos puede alterarla |
| 10 | La IA inventa una respuesta o expone datos | Todo texto de IA es un borrador que una persona aprueba; el modelo corre en el laboratorio (Ollama) y no recibe datos de clientes en servicios externos; el flujo funciona con la IA apagada | Una persona que aprueba sin leer; la lista de verificación del PR ayuda |
| 11 | Código generado con IA trae fallos o dependencias inventadas | Lista de verificación en la plantilla de PR, SAST (bandit), análisis de dependencias, revisión de otra persona | Cambios revisados con prisa antes de la defensa |
| 12 | Caída o pérdida de datos | Respaldo y restauración de PostgreSQL, respaldo de Gitea y Argo CD fuera del nodo, simulaciones de falla | El laboratorio corre en un solo nodo |
| 13 | La voz expone un secreto o se transcribe mal | El audio no se guarda y pasa solo por la red del laboratorio; la transcripción se muestra y se corrige antes de enviarla, y se le tapan los secretos (spec 020); el servicio limita tamaño, duración y turnos y acepta un token; la voz no ejecuta acciones | Una persona que envía sin revisar (opción «enviar sin revisar»); el micrófono exige HTTPS o localhost |

## Lo que no cubre (decisiones conscientes)

- Un adversario con acceso al nodo o a la cuenta de administrador del clúster.
- Denegación de servicio: la cuota del plan y el escalado del Hub la limitan, pero no hay protección dedicada.
- Kyverno y políticas de admisión adicionales: quedan como mejora; hoy basta la política de registro y etiqueta.
