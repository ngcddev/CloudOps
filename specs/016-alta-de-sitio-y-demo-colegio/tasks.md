# Tareas 016 · Alta de sitio por GitOps y demo del colegio

## Alta de sitio

- [x] T01 · Crear archivos nuevos en Gitea y comprobar imágenes — **Verifica:** `test_provisioning.py`.
- [x] T02 · Generar los manifiestos del sitio — **Verifica:** idénticos a los de restaurante, ferretería y consultorio.
- [x] T03 · Endpoint de alta con 201/409/422/403/404 y bitácora — **Verifica:** 11 pruebas.
- [x] T04 · ApplicationSet `clientes` — **Verifica:** el colegio queda Synced/Healthy en 40 s.
- [x] T05 · Botón «Dar de alta en GitOps» en la ficha del cliente — **Verifica:** `tsc` sin errores.

## Colegio y demo

- [x] T06 · Plantilla `apps/colegio` v1/v2 e imágenes en el registro — **Verifica:** prueba de humo y 12 pruebas del backend.
- [ ] T07 · Espejo y CI en GitHub — **Verifica:** el workflow corre en GitHub y se muestra en la demo.
- [x] T08 · Reinicio y preparación de la demo en el clúster — **Verifica:** `reiniciar-cluster.sh` y `preparar-colegio.sh`.
- [x] T09 · Caso completo con el colegio — **Verifica:** 13 comprobaciones OK, MTTR 1,3 min.
- [ ] T10 · Guion de 15 minutos ensayado 3 veces con tiempos — **Verifica:** ver spec 015.

## Techstack restante (quinta tanda)

- [x] T11 · Respaldo de Gitea y Argo CD fuera del nodo — **Verifica:** `respaldo-plataforma.sh` (se clona hub-gitops del dump).
- [x] T12 · MLflow en el clúster — **Verifica:** modelo `compuerta-asistente` con alias `production` registrado ahí.
- [x] T13 · Runner de Gitea Actions ejercitado — **Verifica:** subir v1 y v2 dispara la puerta sola; dos corridas `ok` en el Hub.
- [x] T14 · Estado remoto de OpenTofu con bloqueo — **Verifica:** `estado-remoto.sh probar`.
- [x] T15 · Backstage con el colegio en el catálogo — **Verifica:** el catálogo lista los 4 clientes tras el alta.

