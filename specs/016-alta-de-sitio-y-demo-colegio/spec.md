# 016 · Alta de sitio por GitOps y demo del colegio

> **Acciona:** Equipo de Sistemas · **Depende de:** 001, 003, 005, 008, 009, 015 · **Estado:** Implementada y probada en el clúster (14 nov 2026)

## Qué y por qué

La demo de 15 minutos del 30 nov empieza con un cliente que **no existe**: se entra con la cuenta de la agencia, se crea el
«Colegio San Marcos» con una landing y un formulario de inscripciones, se publica v1, el cliente pide un cambio, la v2 sale rota,
se abre el incidente, se hace rollback a v1 y se cierra con el rastro completo. Antes, crear un cliente solo guardaba filas en la
base: el sitio había que armarlo a mano. Ahora el Hub da de alta el sitio por GitOps, sin hablar con Kubernetes.

## Historias de usuario

- **HU-1.** Como técnico de la agencia, quiero dar de alta el sitio de un cliente nuevo desde su ficha, para que aparezca en el
  clúster sin pedirle a nadie que cree archivos.
- **HU-2.** Como equipo, quiero un colegio con v1 sana y v2 rota, para mostrar el ciclo completo de un cambio malo.
- **HU-3.** Como equipo, quiero reiniciar la demo en el clúster con un comando, para ensayar siempre desde cero.

## Criterios de aceptación

- [x] CA-1. `POST /api/services/{id}/provision` escribe `clients/<cliente>/` en hub-gitops (kustomization, y backend si la plantilla tiene
  formulario) y el kustomization es **idéntico** al de los clientes sembrados (prueba contra los tres reales).
- [x] CA-2. El kustomization se escribe al final; una segunda llamada responde 409 y no cambia nada; sin la imagen v1 publicada responde 422
  y no escribe nada; solo la agencia puede llamarlo; queda en la bitácora.
- [x] CA-3. Un ApplicationSet de Argo CD crea la Application `cliente-<nombre>` al aparecer la carpeta: el sitio responde 200 y queda
  Synced/Healthy en menos de un minuto (medido: 40 s).
- [x] CA-4. La plantilla `apps/colegio` tiene v1 sana y v2 rota (500 en `/` y `/health`) y pasa su prueba de humo.
- [x] CA-5. El caso completo corre con el colegio (`NS=cliente-colegio bash gitops/pruebas/demo-caso-restaurante.sh`): cambio a v2, incidente P1,
  rollback a v1, mitigado en 48 s (MTTR 1,3 min), rastro en línea de tiempo, historial y bitácora.
- [x] CA-6. `demo/reiniciar-cluster.sh` deja el Hub con datos semilla y retira el sitio del colegio (Argo CD borra la Application y el namespace).
- [ ] CA-7. Espejo del repositorio y CI en GitHub visibles en la demo (tarea T07).

## Fuera de alcance

- Construir imágenes desde el Hub: se publican por el pipeline; el Hub solo comprueba que v1 exista.
- Cambiar el GitOps de runtime a GitHub (ver plan: GitHub como espejo y CI).
