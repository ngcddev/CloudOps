<!-- Secciones 23 a 29 · Matriz resumida, riesgos, runbook, licencias, glosario, referencias y anexos. Fuente: HECHOS.md §23–§29, RESUMEN.md y PENDIENTES-EQUIPO.md. -->

# Matriz de trazabilidad resumida

La Tabla {T:matriz} resume la trazabilidad. La matriz completa, con una fila por requisito, va en el complementario 02 y su columna de estado sale de `resultados.tsv` de la corrida.

::: {custom-style="Table Caption"}
**Tabla {T:matriz}**\
*Matriz de trazabilidad resumida*
:::

| Requisito | Historia | Componente | Prueba | Evidencia | Estado |
|---|---|---|---|---|---|
| RF-01 | HU-08 | API (auth, deps) | PF-01 | B07 | Cumplido |
| RF-04 | HU-01, HU-02 | change_requests | PF-02 | C22 | Cumplido |
| RF-05 | HU-01 | gitops_publish, Argo CD | PF-03 | C21, C22, E20 | Cumplido |
| RF-06 | HU-02 | Puerta de seguridad | PF-04, PF-05 | B06, C23 | Cumplido |
| RF-07 | HU-03 | Blackbox, Alertmanager, incident_alerts | PF-06 | C26 | Cumplido |
| RF-08 | HU-03 | rollback | PF-07 | C25 | Cumplido |
| RF-09 | HU-04, HU-05 | dashboard, kpi | PF-08, PF-09 | C24, E02, E13 | Cumplido (PF-09 por rediseñar) |
| RF-11 | HU-08 | audit | PF-10 | B07, E12 | Cumplido |
| RF-12 | HU-06 | assistant, knowledge | PF-11 | D02 | Cumplido |
| RF-14 | HU-07 | voz | PF-12 | D11, D12 | Cumplido |
| RNF-10 | — | Pruebas | PF-13, PF-14 | B02, B01 | Parcial (H-TEST-01) |
| RNF-11 | — | Laboratorio | — | F01 | Cumplido |

# Análisis de riesgos resumido

El análisis completo, con responsables, está en el complementario 06. El responsable de cada riesgo es todo el equipo.

::: {custom-style="Table Caption"}
**Tabla {T:riesgos}**\
*Principales riesgos técnicos, de seguridad, de IA y de cronograma*
:::

| Riesgo | Tipo | Prob. | Impacto | Mitigación |
|---|---|---|---|---|
| Un `apply` de OpenTofu reescribe clientes existentes (H-IAC-01) | Técnico | Alta (ocurrió) | Alto | Importar los clientes al estado; probar con un inventario temporal; revisar el plan antes de aplicar |
| El equipo con la GPU se apaga o se satura | Técnico | Media | Medio | Degradación probada: el Hub avisa y sigue (F01); modelo de 3B de respaldo |
| Inyección de prompts y exfiltración (H-IA-01, H-IA-02) | IA | Media | Medio | Guarda, prompt v3, redacción y texto plano; redactar también la salida |
| Fuga de secretos al repositorio | Seguridad | Baja | Alto | Gitleaks en el CI y en la puerta; `.env` fuera del repositorio |
| Pérdida de datos | Técnico | Baja | Alto | Respaldo probado dentro y fuera del nodo (B05, C29) |
| Rama `dev` sin protección | Seguridad | Media | Medio | Activar la protección y exigir PR |
| Pruebas que dependen del entorno (H-TEST-01) | Técnico | Media | Bajo | Fijar el modo dentro de las pruebas |
| Cronograma: sustentación el 30 nov | Cronograma | Media | Alto | [COMPLETAR: fechas de ensayo y de congelamiento] |

# Runbook resumido

Los procedimientos críticos se ensayaron en la corrida (Tabla {T:runbook}). Los nueve runbooks completos están en `runbooks/` y en el complementario 05.

::: {custom-style="Table Caption"}
**Tabla {T:runbook}**\
*Procedimientos de operación ensayados*
:::

| Procedimiento | Cómo | Resultado del ensayo |
|---|---|---|
| Arranque del entorno | `docker compose up --build` desde un clon limpio | 23 s en frío con caché de imágenes (F01) |
| Apagado | `docker compose down` | 3 s (F01) |
| Reinicio de un servicio | `docker compose restart api` o `kubectl rollout restart` | API sana en 6 s (F01); web del Hub (F03) |
| Recuperación de Pods | Borrar la réplica; Kubernetes la recrea | 8 s, sin abrir incidente (C28) |
| Rollback de versión | Botón de rollback del incidente (`git revert` en hub-gitops) | MTTR 3,4 min (C25) |
| Respaldo y restauración | `gitops/pruebas/respaldo.sh`; CronJob y respaldo de la plataforma | 23 tablas iguales; Gitea y Argo CD recuperables (B05, C29) |
| Degradación elegante | Sin Ollama y sin voz | El asistente avisa y el resto del Hub funciona (F01) |
| Dejar la demo lista | `entrega/evidencias/dejar-demo-lista.sh` | Base limpia, puerta vuelta a correr, sitios en v1, 9/9 Applications sanas (Z01) |
| Reinicio completo del clúster | `runbooks/reinicio-del-cluster.md` | No ensayado (riesgo de cambio de IP del nodo) |

# Licencias del software

El código del proyecto se distribuye bajo **Apache 2.0** (`LICENSE`), y los avisos de terceros están en `NOTICE` (Tabla {T:licencias}).

::: {custom-style="Table Caption"}
**Tabla {T:licencias}**\
*Licencias con obligaciones o restricciones*
:::

| Software o modelo | Licencia | Uso | Restricción |
|---|---|---|---|
| Qwen2.5 7B-Instruct | Apache 2.0 | LLM del Hub | Conservar el aviso |
| Qwen2.5 3B-Instruct | Qwen Research | Solo comparación | No comercial; no se redistribuye |
| nomic-embed-text | Apache 2.0 | Embeddings | Conservar el aviso |
| faster-whisper | MIT | Voz a texto | Conservar el aviso |
| piper-tts | GPL-3.0-or-later | Texto a voz | La imagen `hub-voz` queda bajo GPL; aislado por HTTP |
| Voz es_MX claude-high | Apache 2.0 | Texto a voz | Conservar el aviso |
| Grafana, Loki, Tempo | AGPL-3.0 | Observabilidad | Publicar los cambios si se modifican y se ofrecen como servicio (aquí se usan sin modificar) |
| psycopg | LGPL-3.0 | Controlador de PostgreSQL | Uso como biblioteca |
| Kubernetes, Argo CD, Backstage, Prometheus, OpenTofu, Trivy, Cosign | Apache 2.0 o MPL-2.0 | Plataforma | — |

*Nota.* Los datasets de evaluación (`ai/eval/*.jsonl`) y los datos semilla son propios y sintéticos. El inventario completo de dependencias sale del SBOM que genera el CI con Syft. [COMPLETAR: adjuntar la tabla regenerada desde el SBOM del CI.]

# Glosario

- **Cloud native:** forma de construir y operar sistemas con contenedores, orquestación, configuración declarativa y automatización, de modo que se puedan reconstruir y recuperar sin pasos manuales.
- **Kubernetes:** orquestador de contenedores que mantiene el estado declarado de las aplicaciones (réplicas, red, configuración).
- **GitOps:** práctica en la que Git es la fuente de verdad del estado deseado y un agente (aquí Argo CD) lo aplica y corrige las diferencias.
- **IaC (infraestructura como código):** definición de la infraestructura en archivos versionados que una herramienta aplica de forma repetible (aquí OpenTofu).
- **DevSecOps:** integración de controles de seguridad en todo el ciclo de desarrollo y entrega.
- **SBOM:** inventario de los componentes y versiones que contiene un artefacto de software.
- **SLSA:** marco de niveles para garantizar la integridad y la procedencia de los artefactos de software.
- **SLI:** indicador medido del servicio, por ejemplo la fracción de sondeos exitosos.
- **SLO:** objetivo para un SLI en un periodo, por ejemplo 99,9 % de disponibilidad mensual.
- **RAG:** generación aumentada con recuperación: el modelo responde con fragmentos recuperados de una base de conocimiento (Lewis et al., 2020).
- **LLM:** modelo de lenguaje grande, entrenado para generar y comprender texto.
- **SLM:** modelo de lenguaje pequeño, con menos parámetros, que corre en hardware modesto.
- **MLOps:** prácticas para versionar, evaluar, desplegar y vigilar modelos de aprendizaje automático.
- **LLMOps:** MLOps aplicado a modelos de lenguaje: prompts versionados, evaluación de respuestas, seguridad y costo.
- **Prompt injection:** ataque que mete instrucciones en la entrada o en el contexto para que el modelo haga algo distinto de lo previsto.
- **Embedding:** vector numérico que representa el significado de un texto.
- **Índice vectorial:** estructura que guarda embeddings para buscar los textos más parecidos a una consulta.
- **Rollback:** volver a una versión anterior que funcionaba.
- **Runbook:** procedimiento escrito, paso a paso, para atender una situación de operación.

# Referencias

::: {custom-style="Referencia"}
Beyer, B., Murphy, N. R., Rensin, D. K., Kawahara, K., & Thorne, S. (Eds.). (2018). *The site reliability workbook: Practical ways to implement SRE*. O'Reilly Media.
:::

::: {custom-style="Referencia"}
Congreso de Colombia. (2012, 17 de octubre). *Ley Estatutaria 1581 de 2012, por la cual se dictan disposiciones generales para la protección de datos personales*. Diario Oficial No. 48.587.
:::

::: {custom-style="Referencia"}
Departamento Nacional de Planeación. (2025). *Documento CONPES 4144: Política nacional de inteligencia artificial*. DNP.
:::

::: {custom-style="Referencia"}
International Organization for Standardization. (2022). *Information security, cybersecurity and privacy protection — Information security management systems — Requirements* (ISO/IEC 27001:2022).
:::

::: {custom-style="Referencia"}
International Organization for Standardization. (2023a). *Information technology — Artificial intelligence — Management system* (ISO/IEC 42001:2023).
:::

::: {custom-style="Referencia"}
International Organization for Standardization. (2023b). *Systems and software engineering — Systems and software Quality Requirements and Evaluation (SQuaRE) — Product quality model* (ISO/IEC 25010:2023).
:::

::: {custom-style="Referencia"}
Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih, W., Rocktäschel, T., Riedel, S., & Kiela, D. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. *Advances in Neural Information Processing Systems, 33*, 9459–9474.
:::

::: {custom-style="Referencia"}
Ministerio de Tecnologías de la Información y las Comunicaciones. (s. f.). *Modelo de seguridad y privacidad de la información (MSPI)*. MinTIC. [COMPLETAR: URL y fecha de consulta]
:::

::: {custom-style="Referencia"}
Open Source Security Foundation. (s. f.). *SLSA specification v1.2*. https://slsa.dev/ [COMPLETAR: fecha de consulta]
:::

::: {custom-style="Referencia"}
Souppaya, M., Scarfone, K., & Dodson, D. (2022). *Secure Software Development Framework (SSDF) version 1.1: Recommendations for mitigating the risk of software vulnerabilities* (NIST Special Publication 800-218). National Institute of Standards and Technology. https://doi.org/10.6028/NIST.SP.800-218
:::

[COMPLETAR: agregar la documentación oficial de Argo CD, OpenTofu, Prometheus, Ollama y las fichas de los modelos en Hugging Face (URL en `docs/modelos/`), con su fecha de consulta.]

# Anexos

## Apéndice A · Diccionario de datos

El diccionario completo (22 tablas y 210 columnas, con tipo, nulabilidad, relación, si es dato personal y descripción) se genera desde los modelos con `python entrega/generar_diccionario.py` y se adjunta como `entrega/datos/diccionario.csv`. [COMPLETAR: insertar la tabla regenerada antes de la entrega.]

## Apéndice B · Guía de acceso al laboratorio (Gitea y paneles)

1. **Crear el clúster:** instalar Docker y k3d. Correr `bash gitops/platform/k3s/crear-cluster.sh` y aplicar la plataforma como indica `gitops/README.md`. Gitea queda dentro del clúster, sembrado con `hub-gitops`.
2. **Nombres en el archivo de hosts:** agregar `127.0.0.1 hub.local restaurante.hub.local ferreteria.hub.local consultorio.hub.local gitea.hub.local argocd.hub.local grafana.hub.local backstage.hub.local mlflow.hub.local`.
3. **Gitea:** entrar a `http://gitea.hub.local/forja-digital/hub-gitops`, donde se ven los commits de versión, los rollback y la pestaña Actions de cada sitio. El usuario administrador se define en `.env.cluster`, que no se versiona.
4. **Paneles:**
   - Argo CD (`https://argocd.hub.local`): la contraseña inicial está en el Secret `argocd-initial-admin-secret`.
   - Grafana (`http://grafana.hub.local`): la contraseña está en el Secret `grafana-admin`.
   - MLflow (`https://mlflow.hub.local`): sin usuario.
   - Hub (`https://hub.local`): usuarios sembrados con la contraseña del Secret `hub-auth`.
5. **Dejar la demo lista:** `bash entrega/evidencias/dejar-demo-lista.sh`.

## Apéndice C · Capturas

::: {custom-style="Figure Caption"}
**Figura {F:hub-inicio}**\
*Consola de la agencia: inicio con los clientes, el SLA y la disponibilidad*
:::

![](entrega/evidencias/2026-11-16_bb5a284/E/capturas/E02-agencia-inicio.png){width=90%}

::: {custom-style="Figure Caption"}
**Figura {F:hub-incidentes}**\
*Consola de la agencia: incidentes*
:::

![](entrega/evidencias/2026-11-16_bb5a284/E/capturas/E09-agencia-incidentes.png){width=90%}

::: {custom-style="Figure Caption"}
**Figura {F:portal}**\
*Portal del cliente: estado y disponibilidad del mes*
:::

![](entrega/evidencias/2026-11-16_bb5a284/E/capturas/E13-portal-inicio.png){width=80%}

*Nota.* Las fallas listadas son las que provocó la verificación el 16 de noviembre de 2026; la demo se reinicia con datos semilla.

::: {custom-style="Figure Caption"}
**Figura {F:argocd}**\
*Argo CD: las nueve Applications Synced y Healthy*
:::

![](entrega/evidencias/2026-11-16_bb5a284/E/capturas/E20-argocd-aplicaciones.png){width=90%}

::: {custom-style="Figure Caption"}
**Figura {F:grafana-lista}**\
*Grafana: carpeta de tableros CloudOps*
:::

![](entrega/evidencias/2026-11-16_bb5a284/E/capturas/E30-grafana-tableros.png){width=85%}

::: {custom-style="Figure Caption"}
**Figura {F:grafana-tablero}**\
*Grafana: tablero de servicio de los sitios*
:::

![](entrega/evidencias/2026-11-16_bb5a284/E/capturas/E31-grafana-tablero.png){width=90%}

::: {custom-style="Figure Caption"}
**Figura {F:mlflow}**\
*MLflow: modelo registrado de la compuerta del asistente*
:::

![](entrega/evidencias/2026-11-16_bb5a284/E/capturas/E40-mlflow-modelos.png){width=85%}

::: {custom-style="Figure Caption"}
**Figura {F:gitea}**\
*Gitea: repositorio hub-gitops con los commits del Hub*
:::

![](entrega/evidencias/2026-11-16_bb5a284/E/capturas/E41-gitea-hub-gitops.png){width=85%}

::: {custom-style="Figure Caption"}
**Figura {F:puerta}**\
*Gitea Actions: corridas de la puerta de seguridad de un sitio*
:::

![](entrega/evidencias/2026-11-16_bb5a284/E/capturas/E42-gitea-puerta-ferreteria.png){width=85%}

::: {custom-style="Figure Caption"}
**Figura {F:voz}**\
*Asistente por voz en un navegador real: respuesta leída en voz alta*
:::

![](entrega/evidencias/2026-11-16_bb5a284/D/capturas-voz/4-respuesta.png){width=85%}

::: {custom-style="Figure Caption"}
**Figura {F:backstage}**\
*Backstage: catálogo con los sitios de los clientes*
:::

![](entrega/evidencias/2026-11-16_bb5a284/D/capturas-backstage/1-catalogo.png){width=85%}

[COMPLETAR: capturas de una corrida del CI en GitHub Actions y del SBOM y la firma de la puerta; hoy existen como registros de texto (B06, C23).]

## Apéndice D · Pendientes del equipo

Todo lo marcado como [COMPLETAR] en este informe está explicado, como pregunta concreta, en `entrega/evidencias/2026-11-16_bb5a284/PENDIENTES-EQUIPO.md`.
