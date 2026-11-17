<!-- Secciones 12 a 15 · Diagramas de arquitectura, modelo de datos, secuencias y casos de uso. Las figuras se generan con entrega/informe/figuras/generar.sh a partir de HECHOS.md §12–§15. -->

# Diagramas de arquitectura

Los diagramas siguen el modelo C4 y muestran los dominios de código, entrega, artefactos, ejecución, plataforma, operación e IA. Sus elementos y relaciones se tomaron del código y de lo que estaba desplegado durante la corrida (Pods, imágenes y políticas de red).

::: {custom-style="Figure Caption"}
**Figura {F:c4-contexto}**\
*Diagrama de contexto (C4, nivel 1)*
:::

![](entrega/informe/figuras/01-c4-contexto.png){width=95%}

*Nota.* Ollama corre en el equipo anfitrión, fuera del clúster; el Hub lo alcanza por una regla de salida explícita (corrida C09).

::: {custom-style="Figure Caption"}
**Figura {F:c4-contenedores}**\
*Diagrama de contenedores (C4, nivel 2)*
:::

![](entrega/informe/figuras/02-c4-contenedores.png){width=100%}

*Nota.* Imágenes desplegadas: `hub-api:v1.17`, `hub-web:v1.12`, `hub-voz:v1.2` (`gitops/hub/*.yaml`); estado de los Pods en la corrida C03.

::: {custom-style="Figure Caption"}
**Figura {F:c4-componentes}**\
*Diagrama de componentes de la API (C4, nivel 3)*
:::

![](entrega/informe/figuras/03-c4-componentes.png){width=100%}

*Nota.* 15 routers con 61 endpoints, más `/livez` y `/health` (`backend/app/routers/`).

::: {custom-style="Figure Caption"}
**Figura {F:despliegue}**\
*Vista de despliegue (modelo 4+1)*
:::

![](entrega/informe/figuras/04-despliegue.png){width=90%}

::: {custom-style="Figure Caption"}
**Figura {F:flujo}**\
*Flujo de datos: publicación, detección, recuperación y asistente*
:::

![](entrega/informe/figuras/05-flujo-datos.png){width=100%}

*Nota.* Las trazas que van a Tempo llevan tiempos y estados, nunca el texto de las preguntas (corrida A06).

# Modelo de datos

La base del Hub tiene 22 tablas, creadas por 17 migraciones lineales (de `0001` a `0017_esquema_afinado`) (Figura {F:er}). El diccionario de datos, con 210 columnas, se genera desde los modelos con `entrega/generar_diccionario.py` y va completo en el Apéndice A.

::: {custom-style="Figure Caption"}
**Figura {F:er}**\
*Diagrama entidad-relación (tablas principales y cardinalidades)*
:::

![](entrega/informe/figuras/06-modelo-er.png){width=95%}

*Nota.* Relaciones tomadas de las claves foráneas de `backend/app/models/`; `alembic_version` no se dibuja.

**Datos personales o sensibles (todos sintéticos):**
- Contacto de cada cliente: nombre, correo y teléfono.
- Usuarios.
- Preguntas al asistente, que se guardan en `ai_queries` después de redactar los secretos.

**Medidas de protección:** acceso por rol y por cliente, contraseñas con bcrypt de 12 rondas, redacción de secretos antes de guardar o enviar al modelo (`backend/app/services/redaccion.py`) y bitácora de auditoría.

**RAG:** los documentos de ayuda y sus trozos, con el embedding como lista numérica, viven en `kb_documents` y `kb_chunks`. El índice de la demo tiene 1 documento y 31 trozos (corrida Z01).

::: {custom-style="Table Caption"}
**Tabla {T:conservacion}**\
*Tiempo de conservación de cada tipo de dato*
:::

| Dato | Dónde | Conservación | Fuente |
|---|---|---|---|
| Datos del Hub | PostgreSQL | Mientras exista el cliente; respaldo con rotación | `gitops/hub/backup.yaml` |
| Métricas | Prometheus | 30 días o 1 GB | `observability/prometheus/deployment.yaml` |
| Registros | Loki | 72 h, de los Pods de clientes y del Hub | `observability/loki/loki.yaml`, `observability/alloy/config.alloy` |
| Trazas | Tempo | 24 h | `observability/tempo/tempo.yaml` |
| Audio de voz | — | No se guarda | `voz/` |

# Diagramas de secuencia

Las cinco secuencias corresponden a flujos que se ejecutaron en la corrida (Figuras {F:seq-rag} a {F:seq-recuperacion}).

::: {custom-style="Figure Caption"}
**Figura {F:seq-rag}**\
*Consulta al asistente con RAG*
:::

![](entrega/informe/figuras/07-seq-rag.png){width=90%}

::: {custom-style="Figure Caption"}
**Figura {F:seq-borradores}**\
*Generación de documentación: borradores del incidente con aprobación humana*
:::

![](entrega/informe/figuras/08-seq-borradores.png){width=90%}

::: {custom-style="Figure Caption"}
**Figura {F:seq-voz}**\
*Flujo multimodal: voz a texto, respuesta y texto a voz*
:::

![](entrega/informe/figuras/09-seq-voz.png){width=90%}

::: {custom-style="Figure Caption"}
**Figura {F:seq-cicd}**\
*Despliegue con puerta de seguridad, doble control y GitOps*
:::

![](entrega/informe/figuras/10-seq-cicd.png){width=95%}

::: {custom-style="Figure Caption"}
**Figura {F:seq-recuperacion}**\
*Recuperación ante una falla: incidente automático y rollback*
:::

![](entrega/informe/figuras/11-seq-recuperacion.png){width=95%}

*Nota.* Tiempos medidos: del corte al incidente, 48–49 s (C26); MTTR con rollback, 3,4 min (C25).

# Diagrama de casos de uso

::: {custom-style="Figure Caption"}
**Figura {F:casos}**\
*Casos de uso y actores*
:::

![](entrega/informe/figuras/12-casos-de-uso.png){width=90%}
