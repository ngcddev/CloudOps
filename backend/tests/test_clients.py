# Pruebas del CRUD de clientes: crear, listar, ver y editar (spec 001, T06 · CA-2 y CA-5).
from app.models import Client


def test_create_client_with_only_name(client):
    response = client.post("/api/clients", json={"name": "Panadería Luz"})

    assert response.status_code == 201
    assert response.json()["name"] == "Panadería Luz"


def test_create_client_cleans_spaces_and_empty_optionals(client):
    response = client.post("/api/clients", json={"name": "  Panadería Luz ", "email": "   "})

    body = response.json()
    assert body["name"] == "Panadería Luz"
    assert body["email"] is None


def test_create_client_belongs_to_the_agency(client, seeded):
    created = client.post("/api/clients", json={"name": "Panadería Luz"}).json()

    assert seeded.get(Client, created["id"]).agency.name == "Forja Digital"


def test_create_client_without_name_explains_in_spanish(client):
    response = client.post("/api/clients", json={})

    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == "El campo «nombre» es obligatorio."


def test_create_client_with_blank_name_is_rejected(client):
    response = client.post("/api/clients", json={"name": "   "})

    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == "El nombre del cliente es obligatorio."


def test_list_clients_in_creation_order(client):
    client.post("/api/clients", json={"name": "Primero"})
    client.post("/api/clients", json={"name": "Segundo"})

    names = [item["name"] for item in client.get("/api/clients").json()]

    assert names == ["Primero", "Segundo"]


def test_get_unknown_client_is_404_in_spanish(client):
    response = client.get("/api/clients/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "El cliente no existe."}


def test_patch_changes_only_sent_fields(client):
    created = client.post("/api/clients", json={"name": "Panadería Luz", "phone": "3001112233"}).json()

    response = client.patch(f"/api/clients/{created['id']}", json={"email": "luz@ejemplo.test"})

    body = response.json()
    assert response.status_code == 200
    assert body["email"] == "luz@ejemplo.test"
    assert body["phone"] == "3001112233"
    assert body["name"] == "Panadería Luz"


def test_patch_rejects_empty_name(client):
    created = client.post("/api/clients", json={"name": "Panadería Luz"}).json()

    response = client.patch(f"/api/clients/{created['id']}", json={"name": " "})

    assert response.status_code == 422


def test_patch_unknown_client_is_404(client):
    assert client.patch("/api/clients/999", json={"name": "X"}).status_code == 404
