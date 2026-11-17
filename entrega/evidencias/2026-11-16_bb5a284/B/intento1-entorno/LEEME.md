# Primer intento del nivel B (fallos causados por el entorno de ejecución, no por el proyecto)

- B01 y B02: la ruta `/tmp/junit.xml` fue convertida por Git Bash a una ruta de Windows y pytest no pudo escribir el JUnit; se repiten con la conversión de rutas desactivada.
- B04: la primera vez el contenedor corrió como usuario sin privilegios y `pip` no instaló `mlflow`, de modo que 2 módulos (21 pruebas) se saltaron: dio 14 pasadas y 2 módulos omitidos. Repetida como root dan 40 pasadas, que es lo que dice el borrador.
- B05: el árbol de trabajo local tenía 93 archivos con finales de línea CRLF aunque `.gitattributes` fuerza LF (el índice de Git estaba en LF). Con CRLF, `respaldar.sh` falla dentro del contenedor (`set: illegal option -`). Se rehicieron esos archivos desde el índice (sin cambiar su contenido). La lista original está en `hallazgo-crlf-arbol-de-trabajo.txt`. Quien clone el repositorio recibe LF.
