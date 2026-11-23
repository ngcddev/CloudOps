<!-- Sección 1 · La ficha va DESPUÉS de la portada APA (ver construir.sh). Fuente: mission.md, README.md, remoto Git. Los datos que solo conoce el equipo quedan como [COMPLETAR]. -->

# Ficha del proyecto

::: {custom-style="Table Caption"}
**Tabla {T:ficha}**\
*Ficha del proyecto*
:::

| Campo | Valor |
|----------------|--------------------------------------|
| Nombre del proyecto | CloudOps Client Hub: centro de operación de servicios digitales para agencias web |
| Programa | Diplomado CloudForge AI 5.0, Unicomfacauca; proyecto integrador (28 de septiembre al 30 de noviembre de 2026) |
| Integrantes y roles | Cuatro ingenieros de sistemas y un ingeniero industrial (modelo de servicio). `[COMPLETAR: nombre y rol de cada integrante]` |
| Organización o caso de estudio | Forja Digital, agencia web ficticia de Popayán (Cauca), y sus clientes de ejemplo: restaurante La Sazón, ferretería El Tornillo y consultorio dental Popayán |
| Repositorio Git | https://github.com/ngcddev/CloudOps |
| Repositorio GitOps | `forja-digital/hub-gitops`, en el Gitea del laboratorio (http://gitea.hub.local). `[COMPLETAR: dirección pública o archivo comprimido del repositorio, si el jurado no accede a la red del laboratorio]` |
| Dashboard | Grafana del laboratorio (https://grafana.hub.local) y tablero del Hub (https://hub.local) |
| MLflow | https://mlflow.hub.local (modelo `compuerta-asistente`, alias `production`) |
| Pipeline | Gitea Actions (`pipelines/puerta.yaml`) y CI de GitHub (`.github/workflows/ci.yml`) |
| Evidencias técnicas | Carpeta `evidencias/` de la entrega y Apéndice A de este informe |
| Versión del documento | `[COMPLETAR: versión, por ejemplo 1.0]` |
| Fecha de entrega | `[COMPLETAR: fecha de entrega]`; sustentación final el 30 de noviembre de 2026 |
| Docente y jurado | `[COMPLETAR: nombre del docente y de los miembros del jurado]` |

::: {custom-style="Nota"}
*Nota.* Elaboración propia. Los nombres `*.hub.local` solo se resuelven en el equipo del laboratorio con las entradas del archivo `hosts` (`hub.local`, `grafana.hub.local`, `argocd.hub.local`, `gitea.hub.local`, `mlflow.hub.local` y `backstage.hub.local`); Backstage solo responde por HTTPS.
:::
