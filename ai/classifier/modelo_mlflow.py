# Empaque de la compuerta del asistente como modelo de MLflow (spec 012, T08): un `pyfunc` que recibe preguntas y
# devuelve la decisión de la compuerta. Es el artefacto que se registra en el Model Registry como
# `compuerta-asistente` y al que se le pone el alias `production`. El Hub no lo carga con MLflow: promover.py baja el
# JSON del alias a backend/app/assets/ y la API lo lee en Python puro (sin MLflow en la imagen).
# Se registra con `python_model="modelo_mlflow.py"` (modelo desde código), así que el archivo debe quedar autosuficiente.
import json

import mlflow
import pandas as pd
from mlflow.models import set_model

try:  # dentro del repositorio
    from app.services.assistant_gate import GateModel
except ImportError:  # dentro del modelo empaquetado (code_paths copia assistant_gate.py)
    from assistant_gate import GateModel


class CompuertaModel(mlflow.pyfunc.PythonModel):
    """Decide si una pregunta trata del Hub (`en_tema`) o no (`fuera_de_tema`)."""

    def load_context(self, context) -> None:
        with open(context.artifacts["clasificador"], encoding="utf-8") as f:
            self._gate = GateModel(json.load(f))

    def predict(self, context, model_input, params=None) -> pd.DataFrame:
        if isinstance(model_input, pd.DataFrame):
            preguntas = model_input["text"].tolist()
        else:
            preguntas = [str(p) for p in model_input]
        decisiones = [self._gate.decide(p) for p in preguntas]
        return pd.DataFrame(
            {
                "label": [d.label for d in decisiones],
                "p_fuera_de_tema": [d.p_fuera_de_tema for d in decisiones],
                "despertar_llm": [d.despertar_llm for d in decisiones],
            }
        )


set_model(CompuertaModel())
