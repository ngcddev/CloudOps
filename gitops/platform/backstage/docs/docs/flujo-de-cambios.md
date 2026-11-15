# Flujo de un cambio

1. **Solicitud.** El cliente (o la agencia) abre un *ticket* de cambio en el Hub con la versión a publicar.
2. **Puerta de seguridad.** Al subir la etiqueta de la versión al repositorio del sitio, Gitea Actions corre la puerta: secretos, pruebas, construcción, vulnerabilidades, configuración, SBOM, licencias, firma y verificación. El resultado llega al Hub.
3. **Aprobación.** Una persona de la agencia aprueba la solicitud en el Hub; sin la puerta en `ok` no se puede.
4. **Publicación.** El Hub escribe un único commit en `hub-gitops` que cambia la etiqueta de la imagen del sitio.
5. **Sincronización.** Argo CD ve el commit y actualiza el sitio.
6. **Vigilancia.** Prometheus sondea `/health`; si falla 30 s seguidos abre un incidente (P1) en el Hub.
7. **Recuperación.** Desde el incidente se pide el *rollback*: el Hub escribe el commit que vuelve a la versión estable y Argo CD lo aplica. Se mide el MTTR.
8. **Cierre.** Un mensaje para el cliente, redactado con ayuda de la IA y aprobado por una persona, y el reporte del mes con el SLO.

## Dar de alta un sitio nuevo

1. En el Hub, en la ficha del cliente, **Dar de alta en GitOps**: escribe `clients/<cliente>/` en `hub-gitops`.
2. El ApplicationSet de Argo CD crea la Application y el sitio aparece en menos de un minuto.
3. En Backstage, **Crear → Sitio de cliente**, para registrarlo en el catálogo.
