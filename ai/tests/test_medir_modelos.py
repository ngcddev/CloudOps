# Pruebas de la medición de modelos (spec 020, T02) sin Ollama: la tabla de la ficha y su actualización en el bloque marcado.
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "ai" / "eval"))
sys.path.insert(0, str(RAIZ / "ai"))

import medir_modelos  # noqa: E402

CHAT = {"modelo": "qwen2.5:7b-instruct", "tipo": "chat", "repeticiones": 3, "arranque_en_frio_s": 12.5, "carga_s": 8.5, "latencia_media_s": 3.6,
        "tokens_por_s": 33.7, "memoria_total_mib": 4535, "vram_mib": 4535, "fecha_utc": "2026-11-15T06:00:00+00:00"}
EMBED = {"modelo": "nomic-embed-text", "tipo": "embeddings", "repeticiones": 3, "arranque_en_frio_s": 0.1, "latencia_media_s": 0.08, "textos_por_s": 100.0,
         "memoria_total_mib": 320, "vram_mib": 320, "fecha_utc": "2026-11-15T06:00:00+00:00"}


def test_la_tabla_de_un_modelo_de_chat_trae_velocidad_memoria_y_fecha():
    tabla = medir_modelos.linea_ficha(CHAT)

    assert "33.7 tokens/s" in tabla and "4535 MiB / 4535 MiB" in tabla and "Medido el 2026-11-15" in tabla


def test_la_tabla_de_embeddings_mide_textos_por_segundo():
    assert "100.0 textos/s" in medir_modelos.linea_ficha(EMBED)


def test_actualizar_la_ficha_reemplaza_solo_el_bloque_marcado(tmp_path, monkeypatch):
    monkeypatch.setattr(medir_modelos, "FICHAS", tmp_path)
    ficha = tmp_path / "qwen2.5-7b-instruct.md"
    ficha.write_text("# Ficha\n\n## Medición\n\n<!-- medicion:qwen2.5:7b-instruct -->\nPendiente de medir.\n<!-- /medicion -->\n\n## Límites\n\nTexto propio.\n", encoding="utf-8")

    assert medir_modelos.actualizar_ficha(CHAT) is True
    texto = ficha.read_text(encoding="utf-8")

    assert "Pendiente de medir" not in texto and "| Velocidad | 33.7 tokens/s |" in texto
    assert texto.startswith("# Ficha") and texto.rstrip().endswith("Texto propio.")


def test_una_ficha_sin_el_bloque_no_se_toca(tmp_path, monkeypatch):
    monkeypatch.setattr(medir_modelos, "FICHAS", tmp_path)
    (tmp_path / "qwen2.5-7b-instruct.md").write_text("# Ficha sin bloque\n", encoding="utf-8")

    assert medir_modelos.actualizar_ficha(CHAT) is False
