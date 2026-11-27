# 024 · CloudOps Hub en producción en la nube (GCP) con la IA local por túnel

> **Acciona:** Equipo de Sistemas (Cloud / Platform) · Industrial valida costo y calendario de apagado
>
> **Módulo:** 7 (entrega) · **Requerimientos:** RNF de disponibilidad y de privacidad de datos · **Depende de:** 003, 005, 011, 021, 022 · **Estado:** Spec y plan

## Qué y por qué

Hasta hoy el Hub vive en un laboratorio local (k3d en el PC del equipo). Para las pruebas del 27–28 nov y la sustentación del 30 nov se quiere que **todo el Hub corra en la nube**, accesible por HTTPS desde cualquier lugar, sin depender del PC para nada salvo la inteligencia artificial. El modelo de lenguaje (Ollama, qwen2.5:7b y nomic-embed) sigue en el equipo de Nicolás y la nube lo alcanza por un túnel privado. Así se cumple la regla de que los datos de clientes no salen a servicios de IA externos. Si el PC de la IA está apagado, el asistente avisa y el resto del Hub sigue funcionando (ya es así hoy).

El costo se cubre con la prueba gratuita de Google Cloud (300 USD, 90 días). La máquina se apaga entre fechas para no gastar crédito.

## Actores

| Actor | Qué hace en esta spec |
|---|---|
| Técnico de la agencia | Entra al Hub por una dirección HTTPS pública y opera igual que en el laboratorio |
| Cliente final | Abre su sitio por HTTPS |
| Responsable de la nube (Nicolás) | Crea la cuenta, el proyecto y las claves; enciende y apaga la máquina |
| Industrial / cumplimiento | Revisa el costo, las alertas de presupuesto y el calendario de encendido |

## Historias de usuario

- **HU-1.** Como técnico, quiero abrir el Hub por una dirección HTTPS pública, para operar y presentar sin estar en la red del laboratorio.
- **HU-2.** Como responsable de la nube, quiero que la máquina, la red y el cortafuegos se creen desde código, para repetirlos y borrarlos sin tocar la consola.
- **HU-3.** Como responsable de privacidad, quiero que la IA corra en el equipo del equipo y se alcance por un túnel autenticado, para que ningún dato de cliente llegue a un servicio externo.
- **HU-4.** Como responsable de costos, quiero un presupuesto con alertas y un modo de apagado, para no pasarme del crédito.
- **HU-5.** Como técnico de guardia, quiero un respaldo fuera de la máquina y un procedimiento de recuperación, para no perder el Hub si la máquina falla.

## Criterios de aceptación

- [ ] CA-1. El Hub y los 3 sitios de clientes responden por HTTPS con certificado válido desde fuera de la red del equipo.
- [ ] CA-2. Argo CD en la nube aplica un cambio de versión de un sitio en menos de 1 minuto, igual que en el laboratorio.
- [ ] CA-3. Con el PC de la IA encendido, el asistente responde en modo RAG por el túnel; con el PC apagado, el asistente avisa «sin IA» y el resto de pantallas funciona.
- [ ] CA-4. La IA no tiene puerto abierto a Internet: el túnel exige autenticación y el cortafuegos de la nube solo abre 80 y 443 (y 22 restringido a la IP del equipo).
- [ ] CA-5. Los contenedores corren sin root y las pruebas de humo del Hub y los sitios pasan con 0 fallos en la nube.
- [ ] CA-6. `tofu destroy` y `tofu apply` recrean la máquina y la red sin pasos manuales fuera del arranque documentado.
- [ ] CA-7. Existe un presupuesto con alertas a 10, 25 y 50 USD y un procedimiento de apagado y encendido probado.
- [ ] CA-8. Hay un respaldo de la base y de la plataforma fuera de la máquina y se probó restaurarlo.

## Fuera de alcance

- Alta disponibilidad, varios nodos o balanceador administrado.
- Dominio propio (se usa sslip.io).
- GPU en la nube: la IA sigue local.
- Migrar la versión de desarrollo (docker compose) a la nube.
- Cambios al funcionamiento de la aplicación.

## Demo de cierre

1. Abrir el Hub por su dirección HTTPS desde un teléfono con datos móviles; iniciar sesión.
2. Abrir los 3 sitios de clientes.
3. Publicar una versión nueva de un sitio y ver a Argo CD aplicarla.
4. Preguntar al asistente con el PC de la IA encendido; luego apagar Ollama y repetir.
5. Mostrar el presupuesto y apagar la máquina con el script.
