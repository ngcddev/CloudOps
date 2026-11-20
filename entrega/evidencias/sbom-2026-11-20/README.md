# SBOM de las imágenes desplegadas (20 nov 2026)

Generado con Syft v1.55.0 sobre `hub-api:v1.18`, `hub-web:v1.12` y `hub-voz:v1.2`, en formato SPDX (`*.spdx.json`) y en el de Syft (`*.syft.json`).
La tabla de componentes sale de `python entrega/tabla_sbom.py entrega/evidencias/sbom-2026-11-18` (`tabla-sbom.md` y `tabla-sbom.csv`).

A los `*.syft.json` se les quitó `source.metadata.config` (la configuración de la imagen, con las variables de entorno de la imagen base, por ejemplo `GPG_KEY`, la huella
pública de la clave con la que firma Python): no es un secreto, pero Gitleaks la marca. Los artefactos y las licencias, que es lo que usa la tabla, quedan intactos.
