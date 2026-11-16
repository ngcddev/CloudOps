# Credenciales para curl sin ponerlas en la línea de comandos (spec 022, T37; auditoría IA-05). Con `-u usuario:clave` la contraseña es un argumento del proceso y cualquiera con
# `ps` (o `docker inspect`) la lee mientras corre. Aquí viaja por un descriptor de archivo anónimo: curl lee `user = ...` de su entrada estándar con `-K -` y en la lista
# de procesos no aparece. (No se usa `-K <(...)`: el curl nativo de Windows que trae Git Bash no lee /dev/fd.) Uso:  cred_curl "$USUARIO" "$CLAVE" | curl -sS -K - https://...
# Como `-K -` ocupa la entrada estándar, esa llamada no puede además leer el cuerpo con `-d @-`: se pasa con `-d "$cuerpo"`.
cred_curl() {
  local usuario="${1//\\/\\\\}" clave="${2//\\/\\\\}"
  usuario="${usuario//\"/\\\"}"; clave="${clave//\"/\\\"}"
  printf 'user = "%s:%s"\n' "$usuario" "$clave"
}
