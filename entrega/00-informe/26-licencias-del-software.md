<!-- GENERADA por entrega/generar_tablas.py a partir de entrega/datos/licencias.csv. No editar a mano. -->

# Licencias del software

Se registran 57 componentes, modelos y conjuntos de datos con su versión, licencia, uso y restricciones. Las licencias de las dependencias directas de Python y de JavaScript se leyeron de los metadatos de los paquetes instalados y del `package-lock.json` el 16 de noviembre de 2026; las de los modelos, de sus fichas (verificadas el 15 de noviembre de 2026 en Hugging Face y en la página de Ollama); las de la plataforma y de las herramientas son las que declara cada proyecto y **no se verificaron de nuevo en esta revisión**, por lo que deben confirmarse en el repositorio de cada proyecto antes de redistribuir. Las dependencias transitivas y los paquetes del sistema de las imágenes base no se listan: su inventario y sus licencias están en el SBOM (SPDX) que la puerta genera para cada imagen.

## Lo que condiciona el uso

Estas son las licencias que imponen condiciones o que quedan sin definir:

- **psycopg** (LGPL-3.0-only): Se usa como biblioteca sin modificarla. Al redistribuir la imagen hay que conservar el aviso y permitir reemplazar la biblioteca.
- **piper-tts (motor)** (GPL-3.0-or-later): Corre en un servicio aparte al que el Hub llama por HTTP. Si la imagen hub-voz se entrega a un tercero hay que acompañarla de su código fuente.
- **Docker Desktop y Docker Engine** (Engine: Apache-2.0. Desktop: términos comerciales de Docker): Docker Desktop tiene condiciones de uso según el tamaño y el tipo de organización: confirmarlas antes de usarlo fuera del entorno académico.
- **Grafana** (AGPL-3.0): Si se modifica y se ofrece como servicio en red hay que publicar el código modificado. Aquí se usa sin modificar.
- **Grafana Loki** (AGPL-3.0): Igual que Grafana.
- **Grafana Tempo** (AGPL-3.0): Igual que Grafana.
- **Terraform** (BUSL-1.1): Uso restringido en productos que compitan con HashiCorp: no se usa en producción.
- **Qwen2.5 3B Instruct** (Qwen Research License (solo investigación)): No se usa en producción ni se redistribuye.
- **Compuerta del asistente** (Sin definir): El repositorio no tiene archivo de licencia.
- **Preguntas de evaluación, datos de entrenamiento de la compuerta y datos semilla** (Sin definir): El repositorio no tiene archivo de licencia.
- **Debian (python:3.12-slim), Alpine y Node 22** (Licencias de cada paquete (GPL, LGPL, MIT, BSD y otras)): Las licencias de los paquetes del sistema se pueden consultar en el SBOM de cada imagen.

**El código del proyecto no tiene licencia.** El repositorio no incluye un archivo `LICENSE`, y sin él el código se publica con todos los derechos reservados por defecto, aunque algunos documentos del repositorio lo describan como abierto. `[COMPLETAR: licencia del código del proyecto (por ejemplo MIT o Apache-2.0) y del material propio de evaluación; luego agregar el archivo LICENSE]`

## Aplicación (Python)

::: {custom-style="Table Caption"}
**Tabla {T:lic-1}**\
*Licencias: aplicación (python)*
:::


| Componente | Versión | Licencia | Uso en el proyecto | Restricciones |
|------------------------|----------|----------------|----------------------|----------------------------------|
| FastAPI | 0.142.2 | MIT | API del Hub y servicio de voz | Ninguna relevante |
| Uvicorn | 0.54.0 | BSD-3-Clause | Servidor de la API | Ninguna relevante |
| SQLAlchemy | 2.1.1 | MIT | Acceso a datos | Ninguna relevante |
| Alembic | 1.20.0 | MIT | Migraciones | Ninguna relevante |
| psycopg | 3.3.6 | LGPL-3.0-only | Controlador de PostgreSQL | Se usa como biblioteca sin modificarla. Al redistribuir la imagen hay que conservar el aviso y permitir reemplazar la biblioteca |
| pydantic-settings | 2.15.0 | MIT | Configuración | Ninguna relevante |
| bcrypt | 5.0.0 | Apache-2.0 | Hash de contraseñas | Conservar el aviso de licencia |
| PyJWT | 2.15.1 | MIT | Tokens de sesión | Ninguna relevante |
| ReportLab | 5.1.0 | BSD | Reportes en PDF | Ninguna relevante |
| OpenTelemetry (SDK, exportador e instrumentación) | 1.45.2 y 0.66b2 | Apache-2.0 | Trazas | Conservar el aviso de licencia |
| faster-whisper | 1.2.1 | MIT | Voz a texto | Ninguna relevante |
| PyAV (av) | 16.1.0 | BSD-3-Clause | Decodificación de audio | Ninguna relevante |
| piper-tts (motor) | 1.8.0 | GPL-3.0-or-later | Texto a voz | Corre en un servicio aparte al que el Hub llama por HTTP. Si la imagen hub-voz se entrega a un tercero hay que acompañarla de su código fuente |


::: {custom-style="Nota"}
*Nota.* Elaboración propia a partir de `entrega/datos/licencias.csv`. Fuente de la licencia: metadatos del paquete, metadatos del paquete y ficha del modelo.
:::


## Aplicación (frontend)

::: {custom-style="Table Caption"}
**Tabla {T:lic-2}**\
*Licencias: aplicación (frontend)*
:::


| Componente | Versión | Licencia | Uso en el proyecto | Restricciones |
|------------------------|----------|----------------|----------------------|----------------------------------|
| React y React DOM | 18.3.1 | MIT | Consola y portal | Ninguna relevante |
| React Router | 6.30.6 | MIT | Navegación | Ninguna relevante |
| Vite | 6.4.3 | MIT | Construcción del frontend | Ninguna relevante |
| TypeScript | 5.6.3 | Apache-2.0 | Tipos y compilación | Conservar el aviso de licencia |
| Fuentes Geist y Geist Mono | 5.3.0 | OFL-1.1 | Tipografía | Pueden redistribuirse con el software, pero no venderse por separado |


::: {custom-style="Nota"}
*Nota.* Elaboración propia a partir de `entrega/datos/licencias.csv`. Fuente de la licencia: package-lock.json.
:::


## Plataforma

::: {custom-style="Table Caption"}
**Tabla {T:lic-3}**\
*Licencias: plataforma*
:::


| Componente | Versión | Licencia | Uso en el proyecto | Restricciones |
|------------------------|----------|----------------|----------------------|----------------------------------|
| Kubernetes distribuido por k3s | v1.32.9-k3s1 | Apache-2.0 | Clúster de un nodo | Ninguna relevante |
| Traefik (entrada de k3s) | 3.3.6 | MIT | Entrada HTTP y HTTPS | Ninguna relevante |
| CoreDNS, metrics-server y local-path-provisioner (de k3s) | 1.12.3, 0.8.0 y 0.0.31 | Apache-2.0 | DNS, métricas y volúmenes | Ninguna relevante |
| k3d | Sin registrar | MIT | Clúster de laboratorio en Docker | Ninguna relevante |
| Argo CD | 2.13.3 | Apache-2.0 | GitOps | Ninguna relevante |
| Redis (de Argo CD) | 7.0.15 | BSD-3-Clause | Caché de Argo CD | Las versiones posteriores a la 7.2 cambiaron de licencia: no actualizar sin revisarla |
| Gitea y su ejecutor de Actions | 1.22.6 y 0.2.13 | MIT | Git, registro de contenedores y puerta de seguridad | Ninguna relevante |
| Backstage | Imagen fijada por digest | Apache-2.0 | Catálogo y plantillas | Ninguna relevante |
| PostgreSQL | 16 (Alpine) | PostgreSQL License | Base de datos del Hub | Ninguna relevante |
| nginx (imagen sin privilegios) | 1.30 | BSD-2-Clause | Servidor de la consola web | Ninguna relevante |
| SeaweedFS | 4.53 | Apache-2.0 | Estado remoto de OpenTofu (laboratorio) | Ninguna relevante |
| Docker Desktop y Docker Engine | 29.9.2 | Engine: Apache-2.0. Desktop: términos comerciales de Docker | Contenedores del laboratorio | Docker Desktop tiene condiciones de uso según el tamaño y el tipo de organización: confirmarlas antes de usarlo fuera del entorno académico |


::: {custom-style="Nota"}
*Nota.* Elaboración propia a partir de `entrega/datos/licencias.csv`. Fuente de la licencia: declarada por el proveedor, declarada por el proyecto.
:::


## Observabilidad

::: {custom-style="Table Caption"}
**Tabla {T:lic-4}**\
*Licencias: observabilidad*
:::


| Componente | Versión | Licencia | Uso en el proyecto | Restricciones |
|------------------------|----------|----------------|----------------------|----------------------------------|
| Prometheus | 3.5.0 | Apache-2.0 | Métricas y alertas | Ninguna relevante |
| Alertmanager | 0.28.1 | Apache-2.0 | Enrutamiento de alertas | Ninguna relevante |
| Blackbox Exporter | 0.27.0 | Apache-2.0 | Sondeo de sitios | Ninguna relevante |
| kube-state-metrics | 2.15.0 | Apache-2.0 | Estado de Kubernetes | Ninguna relevante |
| Grafana Alloy | 1.10.2 | Apache-2.0 | Recolección de registros | Ninguna relevante |
| Grafana | 12.1.1 | AGPL-3.0 | Tableros | Si se modifica y se ofrece como servicio en red hay que publicar el código modificado. Aquí se usa sin modificar |
| Grafana Loki | 3.5.3 | AGPL-3.0 | Registros | Igual que Grafana |
| Grafana Tempo | 2.8.2 | AGPL-3.0 | Trazas | Igual que Grafana |


::: {custom-style="Nota"}
*Nota.* Elaboración propia a partir de `entrega/datos/licencias.csv`. Fuente de la licencia: declarada por el proyecto.
:::


## Entrega y seguridad

::: {custom-style="Table Caption"}
**Tabla {T:lic-5}**\
*Licencias: entrega y seguridad*
:::


| Componente | Versión | Licencia | Uso en el proyecto | Restricciones |
|------------------------|----------|----------------|----------------------|----------------------------------|
| Gitleaks | 8.30.1 | MIT | Secretos | Ninguna relevante |
| Trivy | 0.76.1 | Apache-2.0 | Vulnerabilidades y configuración | Ninguna relevante |
| Syft | 1.55.0 | Apache-2.0 | SBOM | Ninguna relevante |
| Cosign | 3.1.4 | Apache-2.0 | Firma y verificación | Ninguna relevante |
| bandit, ruff y pytest | ruff 0.14.0, pytest 9.1.1 y bandit sin fijar | Apache-2.0, MIT y MIT | Análisis estático, lint y pruebas | Solo en desarrollo y CI |


::: {custom-style="Nota"}
*Nota.* Elaboración propia a partir de `entrega/datos/licencias.csv`. Fuente de la licencia: declarada por el proyecto.
:::


## Infraestructura como código

::: {custom-style="Table Caption"}
**Tabla {T:lic-6}**\
*Licencias: infraestructura como código*
:::


| Componente | Versión | Licencia | Uso en el proyecto | Restricciones |
|------------------------|----------|----------------|----------------------|----------------------------------|
| OpenTofu | 1.13.2 | MPL-2.0 | Infraestructura como código | Si se modifican archivos de OpenTofu, esos archivos siguen la MPL |
| Terraform | 1.17.0 | BUSL-1.1 | Solo comprueba la compatibilidad del código | Uso restringido en productos que compitan con HashiCorp: no se usa en producción |
| Helm y kubectl con Kustomize | 4.3.2 y 1.32.9 | Apache-2.0 | Chart equivalente y manifiestos | Ninguna relevante |
| Proveedores kubernetes y gitea | 3.4.0 y 0.8.1 | MPL-2.0 y MIT | Recursos de OpenTofu | Ninguna relevante |


::: {custom-style="Nota"}
*Nota.* Elaboración propia a partir de `entrega/datos/licencias.csv`. Fuente de la licencia: declarada por el proyecto.
:::


## IA y MLOps

::: {custom-style="Table Caption"}
**Tabla {T:lic-7}**\
*Licencias: ia y mlops*
:::


| Componente | Versión | Licencia | Uso en el proyecto | Restricciones |
|------------------------|----------|----------------|----------------------|----------------------------------|
| MLflow | 3.18.0 | Apache-2.0 | Registro de modelos | Ninguna relevante |
| Ollama | 0.40.16 | MIT | Servidor de modelos locales | Ninguna relevante |


::: {custom-style="Nota"}
*Nota.* Elaboración propia a partir de `entrega/datos/licencias.csv`. Fuente de la licencia: declarada por el proyecto.
:::


## Modelo

::: {custom-style="Table Caption"}
**Tabla {T:lic-8}**\
*Licencias: modelo*
:::


| Componente | Versión | Licencia | Uso en el proyecto | Restricciones |
|------------------------|----------|----------------|----------------------|----------------------------------|
| Qwen2.5 7B Instruct | Q4_K_M | Apache-2.0 | Asistente, borradores y diagnóstico | Ninguna relevante |
| Qwen2.5 3B Instruct | Q4_K_M | Qwen Research License (solo investigación) | Solo comparación | No se usa en producción ni se redistribuye |
| nomic-embed-text | F16 | Apache-2.0 | Embeddings del RAG | Ninguna relevante |
| faster-whisper small y base | int8 | MIT | Voz a texto | Ninguna relevante |
| Voz Piper es_MX-claude-high | ONNX | Apache-2.0 | Texto a voz | Ninguna relevante |
| Compuerta del asistente | Versión 1 | Sin definir | Clasificador propio | El repositorio no tiene archivo de licencia |


::: {custom-style="Nota"}
*Nota.* Elaboración propia a partir de `entrega/datos/licencias.csv`. Fuente de la licencia: ficha del modelo, ficha del modelo (15 nov 2026).
:::


## Datos

::: {custom-style="Table Caption"}
**Tabla {T:lic-9}**\
*Licencias: datos*
:::


| Componente | Versión | Licencia | Uso en el proyecto | Restricciones |
|------------------------|----------|----------------|----------------------|----------------------------------|
| Preguntas de evaluación, datos de entrenamiento de la compuerta y datos semilla | — | Sin definir | Escritos por el equipo. No se usan conjuntos de datos de terceros | El repositorio no tiene archivo de licencia |


::: {custom-style="Nota"}
*Nota.* Elaboración propia a partir de `entrega/datos/licencias.csv`. Fuente de la licencia: revisión del repositorio.
:::


## Base de contenedores

::: {custom-style="Table Caption"}
**Tabla {T:lic-10}**\
*Licencias: base de contenedores*
:::


| Componente | Versión | Licencia | Uso en el proyecto | Restricciones |
|------------------------|----------|----------------|----------------------|----------------------------------|
| Debian (python:3.12-slim), Alpine y Node 22 | 3.12 y 22 | Licencias de cada paquete (GPL, LGPL, MIT, BSD y otras) | Imágenes base | Las licencias de los paquetes del sistema se pueden consultar en el SBOM de cada imagen |


::: {custom-style="Nota"}
*Nota.* Elaboración propia a partir de `entrega/datos/licencias.csv`. Fuente de la licencia: sbom de la puerta.
:::

