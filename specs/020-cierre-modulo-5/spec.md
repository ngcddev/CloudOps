# 020 · Cierre del módulo 5 (MLOps, LLMOps y serving de IA local)

> **Acciona:** Equipo de Sistemas · **Módulo:** 5 · **Depende de:** 012, 016, 019 · **Estado:** En curso

## Qué y por qué

El contraste con el temario del módulo 5 dejó brechas: no hay ficha por modelo ni análisis de privacidad y riesgos de IA (entregable 13), no se miden la latencia y la
memoria de los modelos, la deriva solo se resume en un porcentaje sin ventanas ni umbral, `promover.py` no compara ni permite volver atrás, y la seguridad de la IA tiene
huecos: las preguntas se guardan y se envían al modelo con lo que la persona escriba (incluidos secretos), los modelos no tienen su integridad comprobada y no se prueban
documentos maliciosos en el corpus de ayuda. El módulo pesa el 15 % y alimenta el 15 % de IA local del proyecto integrador.

## Criterios de aceptación

- [x] CA-1. Cada modelo en uso (Qwen2.5 3B y 7B, nomic-embed-text y la compuerta) tiene su ficha con licencia, origen, digest, uso, límites y riesgos, y existe el análisis de privacidad y riesgos de IA; una prueba comprueba que ningún modelo en uso se queda sin ficha.
- [x] CA-2. Un script mide latencia, tokens por segundo y memoria de cada modelo y lo registra en MLflow (o en JSON si MLflow no responde); las cifras están en las fichas.
- [x] CA-3. La deriva se calcula por ventanas de tiempo (decisiones corregidas, reparto de etiquetas y latencia) con un umbral que la marca, y se expone con las estadísticas del asistente.
- [ ] CA-4. `promover.py` compara el candidato con el modelo en producción y no promueve si empeora; `--rollback` devuelve el alias a la versión anterior.
- [ ] CA-5. Los secretos se redactan antes de guardar la pregunta y de enviarla al modelo; la integridad del clasificador y de los modelos de Ollama se comprueba por suma de verificación; el corpus con instrucciones escondidas no se obedece.

## Fuera de alcance

- Kubeflow, ComfyUI y el componente multimodal (módulo 6) y el despliegue del modelo en el PC B.
