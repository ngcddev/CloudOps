#!/usr/bin/env bash
# REEMPLAZADO por gitops/sincronizar-hub-gitops.sh (spec 022). Este script copiaba carpetas elegidas a mano y reemplazaba la carpeta destino completa: aplicado a
# `gitops/clients/<cliente>` pisaba la versión (images.newTag) que escribe el Hub, y no comprobaba que lo que subía estuviera revisado. El nuevo conoce quién escribe qué en
# hub-gitops, no pisa lo del Hub, solo promueve commits limpios y mezclados, y tiene --simular y --comprobar. Uso:
#     GITEA_USER=... GITEA_PASSWORD=... bash gitops/sincronizar-hub-gitops.sh [--simular]
echo "Este script ya no se usa: ejecuta  bash gitops/sincronizar-hub-gitops.sh --simular  (y sin --simular para promover). Ver gitops/README.md, «Quién escribe qué en hub-gitops»." >&2
exit 2
