# Primer intento del nivel A (fallos causados por el entorno de ejecución, no por el proyecto)

Siete verificaciones fallaron en la primera corrida por la forma de ejecutarlas en Windows con Git Bash. Se conservan estos registros por transparencia; las repeticiones están en la carpeta `A/`.

- A01 ruff: señaló un archivo sin versionar del borrador del informe (`entrega/preprocesar.py`); el CI solo revisa lo versionado.
- A02 frontend: el contenedor no tenía la carpeta `seed/` que el alias `@seed` necesita (en el Dockerfile llega como contexto adicional).
- A08 PSA: la prueba necesita PyYAML y el Python del equipo no lo tiene; se repite en contenedor.
- A09 sincronizador y A14–A16 smokes: `correr.sh` exportaba `MSYS_NO_PATHCONV=1`, lo que rompe `curl -o /dev/null` (código 23) y los repositorios temporales de git en Git Bash.
