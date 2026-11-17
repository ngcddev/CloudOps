# Lee la respuesta guardada del asistente (JSON) y dice cómo se degradó cuando no hay Ollama: campos, quién respondió y el texto. Lo usa clon-limpio.sh (paso de degradación elegante).
import json
import sys

d = json.load(open(sys.argv[1], encoding="utf-8"))
print("   campos:", sorted(d.keys())[:10])
print("   asistente sin IA -> answered_by =", d.get("answered_by"), "| llm_ok =", d.get("llm_ok"))
print("   respuesta:", (d.get("answer") or d.get("detail") or "")[:160].replace("\n", " "))
