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
