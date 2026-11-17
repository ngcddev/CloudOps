# Primer intento de seis verificaciones del clúster (fallos del entorno de ejecución)

- C08–C12: estos scripts fijan `MSYS_NO_PATHCONV=1`; entonces Git Bash no convierte la ruta de `KUBECONFIG` (formato `/c/Users/...`) a una que kubectl.exe entienda, y kubectl cae a `localhost:8080`. Se repite con `KUBECONFIG` en formato `C:/Users/...`. (Quien corra el laboratorio en Windows debe exportarlo así.)
- C14: la prueba usa por defecto `cliente-colegio`, que no existe hasta que la demo lo crea; se repite con `cliente-restaurante`.
