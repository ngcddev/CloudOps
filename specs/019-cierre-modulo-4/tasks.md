# Tareas 019 · Cierre del módulo 4

- [x] T01 · Runbooks — **Verifica:** `runbooks/` cubre los seis casos y la prueba confirma que los scripts y archivos que citan existen.
- [x] T02 · Alertas con runbook_url — **Verifica:** toda alerta de `observability/prometheus/reglas/` trae `runbook_url` y acción, y `promtool test rules` sigue pasando.
- [x] T03 · Tablero RED y USE — **Verifica:** el tablero está provisionado en Grafana y sus expresiones devuelven datos en Prometheus.
- [x] T04 · Informe de capacidad — **Verifica:** el script lista cada namespace de cliente con uso, cuota y margen en el clúster.
- [x] T05 · AIOps con IA local — **Verifica:** el endpoint devuelve un borrador con hipótesis y runbook sin tocar nada, y queda pendiente de aprobación.
- [x] T06 · Operación responsable y drift de OpenTofu — **Verifica:** el documento trae cifras medidas y el script de drift falla si se cambia algo a mano.
