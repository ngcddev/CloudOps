# Plan 017 · Cierre del módulo 2

Cada tarea es independiente y se prueba en el k3s del equipo antes de pasar a la siguiente. Orden: drift (corta y vistosa) → Backstage → staging → Helm → tutor de IA → menores.

## Decisiones

1. **Drift:** se provoca con `kubectl` sobre un sitio real y se mide el tiempo hasta que Argo CD lo revierte; no se toca Git.
2. **Revisión por pull request:** el flujo del Hub escribe el commit en hub-gitops tras la aprobación humana en el Hub, no hay PR en Gitea. Se mantiene y se explica como revisión equivalente.
