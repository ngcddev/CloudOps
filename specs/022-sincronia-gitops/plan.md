# Plan 022 · Sincronía con hub-gitops

1. **Sincronizador** `gitops/sincronizar-hub-gitops.sh`: mapa de dueños fijo (arriba), `--simular`, precondiciones (árbol limpio en lo que se sube y commit contenido en `origin/dev` u `origin/main`), commit con el SHA y la rama de origen. Para cada cliente que ya existe en `hub-gitops` copia todo salvo `kustomization.yaml` y `catalog-info.yaml` (del Hub).
2. **Chequeo** `gitops/pruebas/sincronia.sh`: misma lógica, solo lectura; sale con 1 si hay diferencias.
3. **Limpieza** de `platform/{argocd,gitea,k3s,namespaces.yaml}` en `hub-gitops` (nadie las lee: Argo CD vigila `clients/*` y `observability`; Backstage lee `platform/backstage` y los `catalog-info`). Se retiran una vez con `--limpiar`.
4. **Argo CD para el Hub:** Application `hub` sobre `hub-gitops/hub`, con `selfHeal` y sin `prune` al principio; se revisa el diff antes de activar la sincronización automática.
5. **Documentación:** «Quién escribe qué en hub-gitops» en `gitops/README.md`, comandos en `CLAUDE.md` y los scripts viejos señalan al nuevo.
