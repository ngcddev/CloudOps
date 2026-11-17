# Primer intento del recorrido de la interfaz (no válido)

El Hub guarda la sesión solo en memoria: al navegar con goto a otra ruta se pierde y vuelve a /login; Grafana por HTTPS no cargaba sus archivos en el navegador de pruebas y los campos de Argo CD no se encontraron. Además el script devolvía 0 aunque las comprobaciones fallaran. Se reescribió para navegar con el menú, usar HTTP en Grafana y fallar si algo no aparece. Estas capturas se conservan solo como registro del intento.
