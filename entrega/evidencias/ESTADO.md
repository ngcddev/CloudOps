# Estado del trabajo de evidencias (traspaso)

> Última actualización: 16–17 nov 2026. Este archivo sirve para retomar el trabajo (con otro modelo o en otra sesión) sin perder el contexto.

## Qué está hecho

**Fase 1: paquete de evidencias, completa.** Carpeta de la corrida: `entrega/evidencias/2026-11-16_bb5a284/` (la corrida se fija en `entrega/evidencias/CORRIDA`).

- `RESUMEN.md`: 83 verificaciones (80 pasaron, 3 fallaron; las 3 son hallazgos del proyecto), cifras clave, hallazgos H-* y lo que no se verificó. Se regenera con `python entrega/evidencias/generar-resumen.py entrega/evidencias/2026-11-16_bb5a284`.
- `cifras.json`: las cifras en formato máquina.
- `resultados.tsv` y un registro por paso en `A/ B/ C/ D/ E/ F/ Z/` (comando, salida completa, código, duración, commit). Los intentos fallidos por el entorno están en las carpetas `intento*` de cada nivel, con su `LEEME.md`.
- Capturas reales: `D/capturas-voz`, `D/capturas-backstage`, `E/capturas` (Hub agencia y portal, Argo CD, Grafana, MLflow, Gitea).
- JUnit de las pruebas del backend: `B/junit-modo-completo.xml` y `B/junit-modo-env.xml`. Corridas de evaluación de la IA: `D/eval-*`, `D/malicioso`, `D/secretos`, `D/borradores`, `D/medicion`, `D/tutor`.

**Pruebas nuevas (T06 y T07 de la spec 020):** `ai/eval/preguntas_exfiltracion.jsonl`, `ai/eval/probar_secretos_en_prompt.py`, `backend/tests/test_exfiltracion_ia.py`.

**La demo del clúster quedó lista** (nivel Z): base del Hub limpia, puerta de seguridad vuelta a correr, ferreteria, restaurante y consultorio en v1, índice del asistente reconstruido, 9 de 9 Applications Synced y Healthy.

## Reproducir

```bash
bash entrega/evidencias/correr.sh A B          # niveles A..F y Z; los de efecto en el clúster (C2, C3) cambian el estado de la demo
bash entrega/evidencias/correr.sh Z            # al terminar, deja la demo lista
```

Notas de entorno (Windows + Git Bash): no exportar `MSYS_NO_PATHCONV` globalmente; `KUBECONFIG` en formato `C:/Users/...`; los cuerpos JSON con tildes enviados con curl se rompen (usar texto sin tildes o un archivo); el `.env` y `.env.cluster` deben existir.

## Cambios en el repositorio (sin commit)

- Corregidos: `observability/pruebas/cronometro.sh` y `publicacion-sana.sh` (segunda cuenta aprobadora), `voz/pruebas/navegador.py` (`bypass_csp`).
- Nuevos: las tres pruebas de arriba, las tareas T06 y T07 en `specs/020-cierre-modulo-5/tasks.md`, y todo `entrega/evidencias/`.
- El `.env` se reconstruyó a partir de los contenedores en marcha (ver `F/intento1-error/LEEME.md`).
- Nada se ha subido ni commiteado.

## Lo que falta (en este orden)

1. ~~Fase 3~~ **Hecha (17 nov):** `HECHOS.md`, `PENDIENTES-EQUIPO.md` y `ERRATAS-BORRADOR.md` están en la carpeta de la corrida. Lo que sigue es completar con el equipo lo pendiente. Texto original del paso: **`HECHOS.md`** en la carpeta de la corrida, organizado por las secciones §1 a §29 del informe y los complementarios 01 a 06, con la fuente de cada dato: `[EJEC]` (un registro de esta corrida), `[CÓDIGO]` (`archivo:línea`) o `[EQUIPO]`. Más `PENDIENTES-EQUIPO.md` y `ERRATAS-BORRADOR.md` (lo que el borrador `entrega/00-informe` dice y la evidencia contradice: ADR-12 sobre la salida de red, Loki también recoge `hub`, la explicación 956 frente a 1.134, tareas T0x de la spec 015, fecha de la prueba de voz, MTTR de 1,3–1,5 min frente a 2,8–3,4 min medido hoy, y las demás de `RESUMEN.md`).
2. ~~Fase 2~~ **Hecha (17 nov):** históricos en `docs/historico/` con aviso; `LICENSE` (Apache-2.0), `NOTICE` y `CONTRIBUTING.md`; README con «Cómo levantarlo» y sin estado caduco; constitución, `specs/README.md` (regenerado con las 24 specs), `docs/proceso.md`, `docs/sdd.md`, `docs/requerimientos.md` y README de carpetas corregidos contra el código; regla nueva en `constitution/conventions.md`. Las 1.132 pruebas siguen pasando con estos cambios. Texto original del paso: **depurar la documentación del repositorio** (mover a `docs/historico/`, quitar las tablas duplicadas que caducan, corregir lo que contradice al código, agregar `LICENSE` Apache-2.0, `NOTICE` y `CONTRIBUTING.md`, instrucciones de arranque en el `README.md`). Plan completo en `C:\Users\ngavi\.claude\plans\claude-tengo-un-problema-humble-yao.md`.
3. ~~Fase 4~~ **Primera versión completa (17 nov):** secciones en `entrega/informe/` (29 secciones, 19 tablas, 23 figuras; diagramas en `entrega/informe/figuras/`), construido con `bash entrega/construir.sh` en `Entrega_Final_CloudForge/` (.docx y vista previa en PDF de 45 páginas). Quedan 20 marcadores `[COMPLETAR]` y 2 `[AUDITAR CON PERPLEXITY]` que dependen del equipo. Texto original del paso: **el informe `00_Informe_Final_Proyecto_Integrador_CloudForge.docx`**, escrito desde `HECHOS.md` (herramientas reutilizables: `entrega/construir.sh`, `entrega/plantilla.docx`, `entrega/generar_diccionario.py`).

## Datos del equipo (decididos o pendientes)

Decididos: licencia Apache-2.0; ramas en `dev` hasta el simulacro; voz como único componente multimodal (ComfyUI y video/3D fuera de alcance por cómputo); declarar el uso de agentes de auditoría con skills en Claude Code; equipo: Nicolás Gaviria Cerón (arquitecto, Sistemas), Sebastián Camilo Paja Barrios, Andrés Felipe Díaz Duque y Eric Sebastián Mesías Rojas (programadores, Sistemas), Yisel Andrea Charo Rivera (cumplimiento, Industrial); repositorio https://github.com/ngcddev/CloudOps; formato APA 7; objetivos y partes interesadas se deducen del producto y llevan `[AUDITAR CON PERPLEXITY]`.

Pendientes: nombre oficial del proyecto, docente, jurado y fecha, la entrevista con la empresa de software de Sebastián, y confirmar las tildes de los nombres.
