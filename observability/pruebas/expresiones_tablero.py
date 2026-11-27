# Saca las expresiones PromQL del tablero de Grafana y las escribe como reglas de grabación, para que `promtool check rules`
# valide su sintaxis (spec 010). `$__range` es una variable de Grafana: aquí se reemplaza por 30d.
import json
import sys
from pathlib import Path

tableros = [json.loads(ruta.read_text(encoding="utf-8")) for ruta in sorted((Path(__file__).parent.parent / "grafana" / "dashboards").glob("*.json"))]
reglas = []
for panel in [p for t in tableros for p in t["panels"]]:
    for destino in panel.get("targets", []):
        if panel.get("datasource", {}).get("type") == "prometheus":
            reglas.append(destino["expr"].replace("$__range", "30d"))
print("groups:\n  - name: tablero\n    rules:")
for i, expr in enumerate(reglas):
    print(f"      - record: tablero:expr{i}\n        expr: {json.dumps(expr, ensure_ascii=False)}")
sys.stderr.write(f"{len(reglas)} expresiones\n")
