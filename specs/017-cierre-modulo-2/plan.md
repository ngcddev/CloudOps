# Plan 017 · Cierre del módulo 2

Cada tarea es independiente y se prueba en el k3s del equipo antes de pasar a la siguiente. Orden: drift (corta y vistosa) → Backstage → staging → Helm → tutor de IA → menores.

## Decisiones

1. **Drift:** se provoca con `kubectl` sobre un sitio real y se mide el tiempo hasta que Argo CD lo revierte; no se toca Git.
2. **Revisión por pull request:** el flujo del Hub escribe el commit en hub-gitops tras la aprobación humana en el Hub, no hay PR en Gitea. Se mantiene y se explica como revisión equivalente.
3. **Staging (T03):** un overlay `clients/<cliente>-staging` con su namespace, su dirección y una cuota menor; el ApplicationSet lo recoge solo. No está en el Hub: una falla ahí no abre incidentes (Alertmanager avisa y el Hub la ignora por ser un namespace desconocido).
4. **Promoción:** `staging/publicar.sh` cambia la versión de staging con un commit; `staging/promover.sh` comprueba que esa versión está lista y sana en staging y, solo entonces, pide el cambio por el camino normal del Hub (ticket → puerta de seguridad → aprobación). Staging prueba la versión; el Hub sigue gobernando producción. Probado con Ferretería El Tornillo: la v2 rota se frena en staging y producción no se toca; la v1.1 sana se promueve.
