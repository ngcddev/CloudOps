# Tareas 022 · Sincronía con hub-gitops

- [x] T01 · Sincronizador con dueños, `--simular` y precondiciones — **Verifica:** una prueba con repositorios locales confirma que no pisa la versión del Hub, que `--simular` no sube nada y que rechaza un árbol sucio o un commit sin mezclar.
- [x] T02 · Chequeo de sincronía — **Verifica:** sale con 0 en sincronía y con 1 listando el archivo distinto.
- [x] T03 · Primera promoción real y limpieza — **Verifica:** los cuatro clientes quedan con el solo lectura publicado por Argo CD y `platform/` de `hub-gitops` solo trae lo que Backstage lee.
- [x] T04 · Hub gestionado por Argo CD — **Verifica:** la Application `hub` queda `Synced` y `Healthy` sin cambiar un Pod de más, y un cambio a mano se revierte.
- [x] T05 · Documentación — **Verifica:** el README dice quién escribe qué y los scripts antiguos remiten al nuevo.
