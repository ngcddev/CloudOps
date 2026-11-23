# Tareas 024 · CloudOps Hub en GCP

> Rama por tarea: `feat/024-tNN-slug`. Responsable de la cuenta y las claves: Nicolás. Nada se crea en GCP sin su confirmación.

## Preparación

- [ ] T01 · Crear proyecto de GCP, vincular la facturación de prueba y activar la API de Compute Engine — **Verifica:** `gcloud compute instances list` responde sin error. [Nicolás]
- [ ] T02 · Instalar `gcloud` y OpenTofu y autenticar con una cuenta de servicio de mínimo privilegio — **Verifica:** `tofu plan` en `infra/tofu/gcp/` corre sin credenciales en el repo. [Nicolás]
- [ ] T03 · Crear presupuesto con alertas a 10, 25 y 50 USD — **Verifica:** el presupuesto aparece en la consola con los tres umbrales. [Nicolás]

## Infraestructura

- [ ] T04 · Módulo OpenTofu de red, IP estática, cortafuegos (80, 443; 22 restringido) y VM e2-standard-2 — **Verifica:** `tofu apply` crea la VM y `tofu plan` posterior no propone cambios. [Nicolás]
- [ ] T05 · Script de inicio que instala k3s y deja el nodo listo — **Verifica:** `kubectl get nodes` muestra el nodo `Ready` en menos de 5 minutos tras el arranque. [Nicolás]
- [ ] T06 · Instalar Gitea, Argo CD y el resto de la plataforma desde `hub-gitops` — **Verifica:** todas las Applications `Synced` y `Healthy`. [Nicolás]
- [ ] T07 · Overlay `nube` con hosts `sslip.io`, cert-manager y Let's Encrypt — **Verifica:** el Hub y los 3 sitios abren por HTTPS con certificado válido (CA-1). [Nicolás]

## IA por túnel

- [ ] T08 · Tailscale en la VM y en el PC de la IA; Ollama escuchando solo en la interfaz privada — **Verifica:** desde un Pod, `curl` a `OLLAMA_URL/api/tags` lista los modelos y desde Internet el puerto 11434 no responde (CA-4). [Nicolás]
- [ ] T09 · Apuntar `OLLAMA_URL` del Hub a la IP del túnel y probar la degradación — **Verifica:** el asistente responde en modo RAG con Ollama encendido y avisa «sin IA» con Ollama apagado (CA-3). [Nicolás]
- [ ] T10 · Respaldo de la IA: qwen2.5:3b en CPU en la VM, apagado por defecto — **Verifica:** documentado y probado una vez con la latencia medida. [Nicolás]

## Operación y seguridad

- [ ] T11 · Publicar las imágenes en un registro de la nube y repasar la puerta de seguridad — **Verifica:** `resembrar-puerta.sh` deja las corridas «ok» y los Pods corren sin root (CA-5). [Nicolás]
- [ ] T12 · Respaldo de la base y de la plataforma a un bucket y prueba de restauración — **Verifica:** se borra un dato, se restaura y el Hub lo recupera (CA-8). [Nicolás]
- [ ] T13 · Scripts `apagar.sh` y `encender.sh` y prueba de ciclo completo — **Verifica:** tras apagar y encender, el Hub vuelve sano en menos de 10 minutos y la IP no cambia (CA-7). [Nicolás]
- [ ] T14 · Prueba de recreación: `tofu destroy` y `tofu apply` — **Verifica:** el entorno vuelve con el arranque documentado y sin pasos fuera de él (CA-6). [Nicolás]

## Cierre

- [ ] T15 · Runbook `runbooks/nube-gcp.md` y anexo de evidencias para el informe — **Verifica:** otra persona del equipo enciende, verifica y apaga la nube solo con el runbook.
- [ ] T16 · Demo: pasos de [spec.md](spec.md#demo-de-cierre) — **Verifica:** todos los criterios de [spec.md](spec.md#criterios-de-aceptación).
