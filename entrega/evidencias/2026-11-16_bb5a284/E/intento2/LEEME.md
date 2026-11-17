# Segundo intento del recorrido (Hub bien; Grafana y métricas no)

El Hub y el portal salieron bien. Grafana no cargaba: el Chromium del contenedor no tenía idioma y Grafana falla con RangeError Incorrect locale information provided (Intl.NumberFormat); se fija locale es-CO. La pantalla de métricas no tiene enlace desde el detalle del cliente: se abre con el enrutador del sitio. El portal no muestra el nombre del negocio sino Hola, Marta: se ajusta lo esperado.
