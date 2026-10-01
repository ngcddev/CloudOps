# Pruebas de planes, SLA y del detalle de los clientes semilla (spec 001 · CA-1, CA-3 y CA-4).


def test_plans_come_from_the_seed(client, seeded):
    plans = client.get("/api/plans").json()

    assert [plan["code"] for plan in plans] == ["basico", "estandar", "premium"]
    assert plans[2]["slo_availability"] == 99.9
    assert plans[0]["monthly_price"] is None  # "por definir" hasta que la industrial lo cierre


def test_sla_policies_list_p1_to_p4(client, seeded):
    policies = client.get("/api/sla-policies").json()

    assert [policy["priority"] for policy in policies] == ["P1", "P2", "P3", "P4"]
    assert policies[0]["response_minutes"] == 15
    assert policies[0]["resolution_minutes"] == 240
    assert policies[0]["clock"] == "24x7"


def test_list_shows_the_three_seed_clients_with_main_service_and_plan(client, seeded):
    clients = client.get("/api/clients").json()

    assert [item["name"] for item in clients] == [
        "Restaurante La Sazón",
        "Ferretería El Tornillo",
        "Consultorio Dental Popayán",
    ]
    assert [item["main_service"]["plan"]["name"] for item in clients] == ["Premium", "Estándar", "Básico"]


def test_client_without_services_has_no_main_service(client, seeded):
    created = client.post("/api/clients", json={"name": "Panadería Luz"}).json()

    listed = [item for item in client.get("/api/clients").json() if item["id"] == created["id"]]

    assert listed[0]["main_service"] is None


def test_detail_of_la_sazon_shows_premium_and_p1_sla(client, seeded):
    first_id = client.get("/api/clients").json()[0]["id"]

    detail = client.get(f"/api/clients/{first_id}").json()

    service = detail["projects"][0]["services"][0]
    assert service["plan"]["name"] == "Premium"
    p1 = detail["sla_policies"][0]
    assert (p1["priority"], p1["response_minutes"], p1["resolution_minutes"]) == ("P1", 15, 240)
