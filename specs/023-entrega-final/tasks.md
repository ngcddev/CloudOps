# Tareas · 023 Entrega final: informe consolidador

> Propuestas el 16 nov 2026. Marcar una tarea solo si su **Verifica** se cumple y se ve.

## Preparar

- [x] T01 · Esqueleto de las 29 secciones, plantilla APA 7 y `entrega/construir.sh` — **Verifica:** el script genera un `.docx` con portada, índice automático y las 29 secciones vacías, en el orden pedido.
- [x] T02 · `entrega/verificar.py` — **Verifica:** falla si falta una sección, si un identificador citado no existe, si una ruta del repo no existe o si hay un marcador sin catalogar.

## Columna vertebral

- [x] T03 · Requisitos ampliados (descripción y criterio por RF; RNF por ISO/IEC 25010 con métrica) leídos contra el código — **Verifica:** cada RF indica estado real y el archivo que lo respalda.
- [x] T04 · Historias de usuario, pruebas funcionales y catálogo de evidencias en `entrega/trazabilidad.csv` — **Verifica:** `verificar.py` no encuentra un requisito sin historia, componente, prueba y evidencia, ni sin estado explícito.

## Decisiones y arquitectura

- [x] T05 · Recorrido del código y del historial de Git para listar los puntos de decisión con su evidencia — **Verifica:** una tabla de candidatos a ADR con archivo, commit o PR y alternativa real; el equipo la revisa antes de redactar.
- [x] T06 · Redactar los ADR aprobados — **Verifica:** cada uno tiene contexto, decisión, alternativas reales, consecuencias, estado y línea «Evidencia» que se puede abrir.
- [x] T07 · Secciones 12 a 15 (arquitectura, datos, secuencias, casos de uso) con marcadores de figura — **Verifica:** cada marcador dice qué elementos y relaciones debe tener; el diccionario de datos coincide con los modelos y las migraciones.

## Secciones técnicas y de cierre

- [x] T08 · Secciones 16 a 22 (CI/CD, IaC, GitOps, observabilidad, MLOps, validación de IA, pruebas) — **Verifica:** cada cifra coincide con el comando o archivo de origen citado.
- [x] T09 · Secciones 3 a 11 narrativas y 23 a 29 de cierre (marco normativo, partes interesadas, licencias, glosario, referencias) — **Verifica:** las 8 normas, los 19 términos del glosario y toda cita con su referencia APA.
- [ ] T10 · Construcción final, revisión del PDF página a página y lista de pendientes — **Verifica:** se cumplen CA-1 a CA-7.

## Hallazgos que se cierran antes de la entrega (propuestas el 20 nov 2026)

- [x] T11 · H-IA-01: la respuesta del modelo pasa por `redactar()` antes de guardarse y mostrarse — **Verifica:** `test_una_respuesta_del_modelo_con_un_secreto_se_tapa_antes_de_guardarse` pasa sin `xfail` y la suite del backend sigue en verde.
- [x] T12 · H-TEST-01: las pruebas que dependen del modo del asistente lo fijan por dentro — **Verifica:** la suite completa pasa con `ASSISTANT_CONTEXT_MODE=completo` y con `ASSISTANT_CONTEXT_MODE=rag`.
- [x] T13 · H-OPS-02: la demo 010 provoca la caída del sitio desde Git (versión rota) y no con `kubectl scale` — **Verifica:** el paso de caída abre el incidente P1 y el tablero lo muestra, sin que Argo CD lo revierta antes.
  - Resultado (20 nov): `gitops/pruebas/demo-010.sh` corrió completa y terminó en «todo OK» (incidente #3, MTTR 5,42 min). Publica la v2 rota por GitOps con una segunda cuenta aprobadora, pide el rollback desde el incidente y apaga Prometheus con el selfHeal de `monitoring` en pausa.
  - Dos trampas que se encontraron al verificarla: (1) Argo CD revisa el repositorio cada 3 minutos y (2) con el selfHeal en pausa igual sincroniza **una vez** una Application si la revisión actual es distinta de la de su última operación de sincronización (un commit que no cambió sus manifiestos no le genera operación). Antes de apagar Prometheus el script fuerza una operación de sincronización de `monitoring` y espera a que termine.
- [x] T14 · H-CVE-01: la puerta falla en «vulnerabilidades» con 4 CVE críticas de `nginx` 1.30.6-r1 (arreglo en 1.30.7-r0; la imagen `nginxinc/nginx-unprivileged:1.30-alpine` aún no lo trae) — **Verifica:** las versiones v1, v1.1 y v2 de los tres sitios vuelven a pasar la puerta en «ok», sea con la imagen base corregida o con una excepción con vencimiento aprobada por el equipo.
  - Resultado (20 nov): excepción de laboratorio aprobada por el equipo en `pipelines/trivy-excepciones.yaml` (archivo de ignorados de Trivy, solo 6 CVE de nginx: las 4 críticas que frenan la puerta y 2 altas que frenan el registro de hallazgos del CI, `expired_at: 2026-12-04`). Las 7 versiones de los 3 sitios quedaron en «ok». **Pendiente al vencer:** cuando nginxinc publique la 1.30.7, reconstruir las imágenes y borrar el archivo.
  - Se corrigió de paso un defecto de la verificación de procedencia (`puerta.sh`): leía solo la primera procedencia firmada del digest y una vieja hacía fallar una versión sana; ahora basta con que alguna, ya verificada con la clave, declare el commit de la versión.
  - El CI de GitHub fallaba por lo mismo en `hub-web` (misma imagen base): `analisis-estatico.sh` y `hallazgos.sh` ahora leen el mismo archivo de excepciones y ambos pasan en local. Las 2 CVE altas (CVE-2026-118899 y CVE-2026-123634) solo las ve el registro de hallazgos; la puerta de los sitios mira solo críticas.
- [x] T15 · Publicar `hub-api` v1.18 con la respuesta del modelo redactada (H-IA-01 en el laboratorio) — **Verifica:** la imagen `hub-api:v1.18` está en el registro de Gitea, Argo CD la aplica a la API sin cortar el servicio, `/health` responde y la prueba `test_una_respuesta_del_modelo_con_un_secreto_se_tapa_antes_de_guardarse` pasa sobre ese código.
  - Resultado (20 nov): imagen publicada con `apps/publicar-imagenes.sh hub-api` y promovida con `gitops/sincronizar-hub-gitops.sh` tras fusionar el PR #217 (hub-gitops `e80fb76`). Argo CD la aplicó a los 15 s y el despliegue terminó a los 30 s; en 44 comprobaciones del Hub y de los 3 sitios durante el reemplazo no falló ninguna. El Pod corre `v1.18` sin root, sin `/app/tests`, con 0 reinicios, `/health` responde 200 y el código en ejecución trae `redactar(respuesta)`. Prueba de humo de la imagen de producción en verde.
  - Asistente en el laboratorio (qwen2.5:7b, modo `rag`): una pregunta normal se responde con los pasos de aprobación; una pregunta con un token inventado se tapa antes de llegar al modelo (`secrets_redacted`) y el token no aparece en la respuesta.
  - Límite de la prueba: **no se pudo provocar con el modelo real que la respuesta traiga un secreto**, así que la redacción de la salida se verifica con la prueba unitaria y con el código desplegado, no de punta a punta.
  - Los documentos que dicen «hub-api v1.17» (informe 00, complementario 06 y Apéndice D con su SBOM) quedan por actualizar.

## Pulido del frontend (propuestas el 20 nov 2026)

- [x] T16 · Selector propio con estilo (`Select`) en lugar del `<select>` nativo, con lista desplegable del mismo diseño que la página (tema claro y oscuro, teclado, lectores de pantalla y celular) — **Verifica:** los 22 selectores de las pantallas de agencia y portal usan el componente, la lista abierta usa los tokens de diseño, se maneja con flechas, Inicio, Fin, Enter, Esc y la primera letra, y `tsc` y `npm run build` pasan.
- [x] T17 · Campos de fecha y de mes propios (`DateField` y `MonthField`) con calendario desplegable en español, semana desde el lunes y día de hoy en la hora de Bogotá, en lugar de `<input type="date">` y `type="month"` — **Verifica:** las 4 pantallas con fechas (bitácora, tablero, métricas del cliente y reportes) los usan, respetan `max`, se manejan con teclado y se ven bien en claro, oscuro y 375 px de ancho.

## Limpieza final del repositorio (propuestas el 26 nov 2026)

- [ ] T18 · Dejar en el repositorio solo lo vigente: salen los constructores de documentos (`entrega/*.py`, `.sh`, `.ps1`, plantilla e `informe/*.md`), el paquete de evidencias crudas, `docs/historico` y `docs/cumplimiento-tecnico.md`; los scripts que preparan la demo pasan a `demo/`. Lo que sale se archiva fuera del repositorio (`CW/CloudOps-archivo`), no se borra — **Verifica:** ningún enlace vivo (README, CONTRIBUTING, constitución, READMEs y scripts) apunta a una ruta que ya no existe, y `dejar-demo-lista.sh` corre desde `demo/`.
  - Resultado (26 nov): hecho en el commit de limpieza; ningún enlace vivo apunta a rutas borradas y los scripts de `demo/` pasan `bash -n`. **Falta verificar** `dejar-demo-lista.sh` contra el clúster encendido; hasta entonces la tarea queda abierta.
- [x] T19 · Revisión de código limpio sin cambiar contratos: encabezado en cada archivo, comentarios y docstrings en español, nombres de código en inglés, sin código muerto ni imports sin usar — **Verifica:** pasan las pruebas del backend y de `ai/`, `ruff check .`, `tsc` y `npm run build`.
  - Resultado (26 nov): unos 380 nombres de funciones, clases y constantes pasaron a inglés en el código de producción (backend, voz, ai, pipelines, gitops y frontend), con sus usos en las pruebas; no cambiaron campos de la API, valores de la base, migraciones, nombres de las pruebas ni opciones de línea de comandos. Encabezado en los 4 archivos que no lo tenían y docstring en 40 funciones. Pasan 1.133 pruebas del backend (6 omitidas), 40 de `ai/`, `ruff check .`, `tsc` y `npm run build`.
  - Quedan en español, a propósito: los nombres de archivo de los scripts que se llaman desde la terminal (`evaluar_voz.py`, `medir_modelos.py`…), los módulos del backend (`registros.py`, `redaccion.py`, `bloqueos.py`…) y las variables locales.
