# 019 · Cierre del módulo 4 (IaC, observabilidad, SRE y operación sostenible)

> **Acciona:** Equipo de Sistemas · **Módulo:** 4 · **Depende de:** 008, 010, 011, 016 · **Estado:** En curso

## Qué y por qué

El contraste con el temario del módulo 4 dejó brechas: no hay runbooks (entregable 14 del diplomado), las alertas no dicen qué hacer, solo existe el tablero de
disponibilidad (faltan RED y USE), no hay un informe de capacidad, la IA local no ayuda a diagnosticar con logs y métricas, y la operación responsable (retención,
uso de recursos) y el drift de OpenTofu no están medidos ni documentados. El módulo pesa el 10 % de la nota y alimenta el 20 % de Kubernetes, GitOps e IaC.

## Criterios de aceptación

- [x] CA-1. Existe `runbooks/` con caída del sitio, rollback, respaldo y restauración, reinicio del clúster, saturación y latencia; una prueba comprueba que lo que citan existe.
- [x] CA-2. Toda alerta lleva `runbook_url` y una acción; una prueba falla si una alerta nueva no los trae.
- [x] CA-3. Un tablero de Grafana muestra RED (tasa, errores, duración) y USE (CPU y memoria frente a la cuota), con expresiones probadas.
- [x] CA-4. Un script informa por namespace el uso frente a la cuota y el margen que queda.
- [x] CA-5. Un incidente puede pedir a la IA local una hipótesis de diagnóstico y un borrador de runbook con logs y métricas; queda como borrador que una persona aprueba.
- [x] CA-6. La política de retención y de recursos está documentada con cifras medidas, y una prueba detecta el drift de OpenTofu (`plan -detailed-exitcode`).

## Fuera de alcance

- Alertas por correo o mensajería externa, y observabilidad multi-clúster.
