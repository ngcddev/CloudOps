{{- /* Namespace del sitio: el indicado o cliente-<cliente>. */ -}}
{{- define "sitio.namespace" -}}
{{- default (printf "cliente-%s" .Values.cliente) .Values.namespace -}}
{{- end -}}
