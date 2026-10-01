# Pruebas de proyectos y servicios de un cliente, con su plan (spec 001, T07 · CA-3 y CA-5).


def _client_and_project(client):
    client_id = client.post("/api/clients", json={"name": "Panadería Luz"}).json()["id"]
    project_id = client.post(f"/api/clients/{client_id}/projects", json={"name": "Sitio web"}).json()["id"]
    return client_id, project_id


def _service(plan, **changes):
    data = {
        "name": "Sitio web",
        "host": "panaderia.hub.local",
        "template": "landing",
        "namespace": "cliente-panaderia",
        "plan_id": plan.id,
    }
    return {**data, **changes}


def test_create_project_for_a_client(client):
    client_id = client.post("/api/clients", json={"name": "Panadería Luz"}).json()["id"]

    response = client.post(f"/api/clients/{client_id}/projects", json={"name": "Sitio web"})

    assert response.status_code == 201
    assert response.json()["services"] == []


def test_create_project_for_unknown_client_is_404(client):
    response = client.post("/api/clients/999/projects", json={"name": "Sitio web"})

    assert response.status_code == 404
    assert response.json() == {"detail": "El cliente no existe."}


def test_create_project_with_blank_name_is_rejected(client):
    client_id = client.post("/api/clients", json={"name": "Panadería Luz"}).json()["id"]

    response = client.post(f"/api/clients/{client_id}/projects", json={"name": "  "})

    assert response.status_code == 422


def test_detail_shows_service_with_its_plan(client, plan):
    client_id, project_id = _client_and_project(client)
    client.post(f"/api/projects/{project_id}/services", json=_service(plan))

    detail = client.get(f"/api/clients/{client_id}").json()

    service = detail["projects"][0]["services"][0]
    assert service["host"] == "panaderia.hub.local"
    assert service["status"] == "operativo"
    assert service["plan"]["code"] == "basico"


def test_service_without_plan_is_rejected_in_spanish(client, plan):
    _, project_id = _client_and_project(client)
    data = _service(plan)
    del data["plan_id"]

    response = client.post(f"/api/projects/{project_id}/services", json=data)

    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == "El servicio necesita un plan."


def test_service_with_unknown_plan_is_404(client, plan):
    _, project_id = _client_and_project(client)

    response = client.post(f"/api/projects/{project_id}/services", json=_service(plan, plan_id=999))

    assert response.status_code == 404
    assert response.json() == {"detail": "El plan no existe."}


def test_service_for_unknown_project_is_404(client, plan):
    response = client.post("/api/projects/999/services", json=_service(plan))

    assert response.status_code == 404
    assert response.json() == {"detail": "El proyecto no existe."}


def test_service_with_unknown_template_is_rejected(client, plan):
    _, project_id = _client_and_project(client)

    response = client.post(f"/api/projects/{project_id}/services", json=_service(plan, template="otra"))

    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"].startswith("El campo «plantilla» tiene un valor no permitido")


def test_service_with_blank_host_is_rejected(client, plan):
    _, project_id = _client_and_project(client)

    response = client.post(f"/api/projects/{project_id}/services", json=_service(plan, host="  "))

    assert response.status_code == 422


def test_duplicate_host_is_409(client, plan):
    _, project_id = _client_and_project(client)
    client.post(f"/api/projects/{project_id}/services", json=_service(plan))

    response = client.post(
        f"/api/projects/{project_id}/services", json=_service(plan, namespace="cliente-otro")
    )

    assert response.status_code == 409
    assert "dirección" in response.json()["detail"]


def test_duplicate_namespace_is_409(client, plan):
    _, project_id = _client_and_project(client)
    client.post(f"/api/projects/{project_id}/services", json=_service(plan))

    response = client.post(
        f"/api/projects/{project_id}/services", json=_service(plan, host="otro.hub.local")
    )

    assert response.status_code == 409
    assert "namespace" in response.json()["detail"]
