# Comprueba que las fixtures de sesión de conftest.py entregan el usuario correcto (spec 007, T06).


def test_as_agency_es_un_tecnico_de_la_agencia(as_agency):
    me = as_agency.get("/api/auth/me")

    assert me.status_code == 200
    assert me.json()["role"] == "agencia"
    assert me.json()["email"] == "tecnico.pruebas@forjadigital.test"


def test_as_client_es_el_usuario_de_la_sazon(as_client):
    me = as_client.get("/api/auth/me").json()

    assert me["role"] == "cliente"
    assert me["email"] == "contacto@lasazon.test"
    assert me["client_id"] is not None


def test_as_user_entrega_la_sesion_de_otro_usuario_sembrado(seeded, as_user):
    me = as_user("contacto@eltornillo.test").get("/api/auth/me").json()

    assert me["email"] == "contacto@eltornillo.test"


def test_el_cliente_sin_sesion_sigue_sin_token(client):
    assert client.get("/api/auth/me").status_code == 401
