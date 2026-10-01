# Pruebas de GET /health (spec 001, T03).


def test_health_ok_when_db_answers(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
