# Tareas 018 · Cierre del módulo 3

- [x] T01 · SAST y SCA en el CI — **Verifica:** el CI corre bandit, `trivy fs` y el escaneo del frontend, y pasan (o sus excepciones tienen razón y vencimiento).
- [ ] T02 · Registro de hallazgos con VEX — **Verifica:** Trivy lee el VEX y el script genera el registro con criticidad, explotabilidad y tratamiento.
- [ ] T03 · SBOM atestado y verificado — **Verifica:** `cosign verify-attestation --type spdxjson` pasa en la puerta y falla con otra clave.
- [ ] T04 · Escenarios «dependencia vulnerable» y «manifiesto con permisos excesivos» — **Verifica:** el simulador se detiene en los dos.
- [ ] T05 · Segregación de funciones — **Verifica:** aprobar el propio cambio responde 403 y otra persona de la agencia sí puede.
- [ ] T06 · Sitios con sistema de archivos de solo lectura — **Verifica:** los sitios siguen sanos en el clúster y `trivy config` no marca KSV-0014 en ellos.
- [ ] T07 · Código generado con IA y modelo de amenazas — **Verifica:** la plantilla de PR trae la lista y el modelo cubre los activos, amenazas y controles del Hub.
