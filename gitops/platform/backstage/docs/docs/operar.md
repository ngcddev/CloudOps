# Operar la plataforma

Todos los comandos se corren desde la raíz del repositorio con `KUBECONFIG` apuntando al clúster.

| Qué | Comando |
|---|---|
| Reiniciar la demo del colegio | `bash demo/reiniciar-cluster.sh` |
| Probar el *drift* (Argo CD corrige cambios a mano) | `bash gitops/pruebas/drift.sh` |
| Simular réplica caída, latencia y saturación | `bash gitops/pruebas/simulaciones.sh` |
| Respaldo de Gitea y Argo CD fuera del nodo | `bash gitops/pruebas/respaldo-plataforma.sh` |
| Respaldo y restauración de PostgreSQL | `bash gitops/pruebas/respaldo.sh` |
| Política de admisión de imágenes | `bash gitops/pruebas/admision.sh` |
| Validar la observabilidad | `bash observability/pruebas/validar.sh` |

## Fallas comunes

- **Un sitio no responde tras un cambio.** Pedir el *rollback* desde el incidente; el sitio vuelve a la versión estable en menos de dos minutos.
- **Argo CD muestra `OutOfSync`.** Alguien cambió el clúster a mano: se corrige solo; si no, revisar que `selfHeal` siga activo.
- **El asistente dice que la IA no está disponible.** Ollama (el PC con GPU) está apagado; la compuerta y el resto del Hub siguen funcionando.
