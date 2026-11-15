# Ficha · Compuerta del asistente

| Campo | Valor |
|---|---|
| Nombre en MLflow | `compuerta-asistente` (alias `production`) |
| Origen | Propio: Naive Bayes entrenado por el equipo (`ai/classifier/train.py`) |
| Licencia | La del repositorio; sin código ni pesos de terceros |
| Archivo | `backend/app/assets/clasificador.json`, con su suma SHA-256 en `backend/app/assets/clasificador.sha256` |
| Datos de entrenamiento | `ai/classifier/data/*.jsonl`: preguntas ficticias etiquetadas `en_tema` y `fuera_de_tema`; la prueba nunca se usa para entrenar |
| Uso | Decide si una pregunta trata del Hub antes de despertar al LLM; ahorra la llamada con lo ajeno al Hub |
| Dónde corre | Dentro de la API del Hub (JSON local), o servido con `mlflow models serve` |
| Datos que recibe | La pregunta; no la guarda el modelo |

## Medición

<!-- medicion:compuerta-asistente -->
Pendiente de medir.
<!-- /medicion -->

## Evaluación

| Métrica (v1, 24 ejemplos de prueba) | Valor |
|---|---|
| Exactitud | 95,8 % |
| Preguntas del Hub que dejó sin LLM (`en_tema_perdidas`) | 0 |
| LLM evitado | 91,7 % |

## Límites

- Pocas preguntas de prueba (24): cifra orientativa. Un exportador (`train.py`) se niega a publicar el modelo si pierde una sola pregunta del Hub.
- Una guarda de vocabulario nunca salta el LLM si aparece un término del Hub («ticket», «SLA», «rollback»…).

## Riesgos

Deriva si cambia lo que la gente pregunta (spec 020, T03) y archivo alterado (se comprueba la suma de verificación). No toma decisiones sobre personas.
