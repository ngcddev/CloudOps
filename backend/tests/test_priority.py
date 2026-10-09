# Pruebas de clasificación de prioridad por impacto y urgencia (spec 004, T04).
import pytest

from app.services.priority import classify


@pytest.mark.parametrize(
    ("impact", "urgency", "expected"),
    [
        ("alto", "alta", "P1"),
        ("alto", "media", "P2"),
        ("alto", "baja", "P3"),
        ("medio", "alta", "P2"),
        ("medio", "media", "P3"),
        ("medio", "baja", "P4"),
        ("bajo", "alta", "P3"),
        ("bajo", "media", "P4"),
        ("bajo", "baja", "P4"),
    ],
)
def test_classify_cubre_las_nueve_combinaciones(impact, urgency, expected):
    assert classify(impact, urgency) == expected


@pytest.mark.parametrize("impact", ["crítico", "", "altoo"])
def test_classify_rechaza_impacto_invalido(impact):
    with pytest.raises(ValueError, match="Impacto inválido"):
        classify(impact, "alta")


@pytest.mark.parametrize("urgency", ["crítica", "", "mediaa"])
def test_classify_rechaza_urgencia_invalida(urgency):
    with pytest.raises(ValueError, match="Urgencia inválida"):
        classify("alto", urgency)