# 018 · Cierre del módulo 3 (DevSecOps y seguridad de la cadena de suministro)

> **Acciona:** Equipo de Sistemas · **Módulo:** 3 · **Depende de:** 006, 007, 016, 017 · **Estado:** En curso

## Qué y por qué

Al contrastar el repositorio con el temario del módulo 3 quedaron brechas: no hay análisis estático ni de composición de las dependencias del código, los hallazgos
aceptados no tienen un registro con decisión, el SBOM no viaja con la imagen, quien pide un cambio puede aprobarlo y dos de las prácticas del temario (dependencia vulnerable y
manifiesto con permisos excesivos) no tienen escenario. El módulo pesa el 15 % de la nota y alimenta el 15 % «DevSecOps y cadena de suministro» del proyecto integrador.

## Criterios de aceptación

- [x] CA-1. El CI corre análisis estático (bandit) y análisis de composición (`trivy fs` sobre las dependencias de Python y npm, y la imagen del frontend); Dependabot vigila las dependencias.
- [x] CA-2. Cada hallazgo aceptado tiene una decisión escrita (VEX con estado, justificación y vencimiento) que Trivy lee, y un script genera el registro desde los reportes.
- [x] CA-3. El SBOM se adjunta a la imagen con Cosign y la puerta lo verifica junto con la procedencia.
- [x] CA-4. El simulador tiene los escenarios «dependencia vulnerable» y «manifiesto con permisos excesivos», y la puerta se detiene en los dos.
- [ ] CA-5. Quien solicita un cambio no puede aprobarlo (segregación de funciones), con la bitácora y la demo al día.
- [ ] CA-6. Los sitios de clientes corren con el sistema de archivos de solo lectura y la excepción KSV-0014 de los sitios se cierra.
- [ ] CA-7. La plantilla de PR tiene la lista de verificación del código generado con IA y existe el modelo de amenazas del Hub.

## Fuera de alcance

- Verificar la firma en la admisión del clúster (Kyverno o policy-controller): cuesta unos 300 a 500 MB de RAM y la verificación vive en la puerta. Queda como mejora anotada.
