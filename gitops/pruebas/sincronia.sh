#!/usr/bin/env bash
# ¿hub-gitops está en sincronía con el repositorio principal? (spec 022). Solo lectura: clona hub-gitops, aplica encima lo que promovería gitops/sincronizar-hub-gitops.sh y dice qué
# archivos serían distintos. Sale con 0 en sincronía y con 1 si hay diferencias (se corrigen con: bash gitops/sincronizar-hub-gitops.sh). No hace falta usuario ni clave (el repo es público).
# Úsalo antes de una demo y después de mezclar un PR que toque gitops/ u observability/. Uso:  bash gitops/pruebas/sincronia.sh
exec bash "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../sincronizar-hub-gitops.sh" --comprobar "$@"
