# Segundo intento (queda el estado del Hub de los intentos anteriores)

- C22, C27, C26: «Ya hay un cambio en curso para este sitio»: los intentos fallidos anteriores dejaron solicitudes de cambio pendientes en la base del Hub. Se repite después de reiniciar la demo del clúster (base del Hub limpia).
- C24: en este intento fallaron más pasos (el monitoreo no abrió el incidente) por el mismo estado sucio; el paso 6 (Prometheus apagado) falló igual que en el primer intento: ver la repetición.
- C30: el binario `k3d` no está instalado en este equipo y `infra/tofu.sh` lo necesita solo para leer el kubeconfig; se usa un sustituto mínimo (`entrega/evidencias/shims/k3d`) que devuelve el kubeconfig del mismo clúster.
