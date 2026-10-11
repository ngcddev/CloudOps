# Pruebas del modelo, migración y semilla de usuarios de la spec 004.
from sqlalchemy import inspect, text


def test_seed_carga_un_usuario_de_agencia_y_tres_de_clientes(seeded):
    users = seeded.execute(text("SELECT name, email, role, client_id FROM users ORDER BY id")).mappings().all()

    assert len(users) == 4
    assert sum(user["role"] == "agencia" for user in users) == 1
    assert sum(user["role"] == "cliente" for user in users) == 3
    assert sum(user["client_id"] is None for user in users) == 1
    assert all("password" not in user for user in users)


def test_tabla_users_tiene_la_estructura_de_t02(seeded):
    columns = {column["name"] for column in inspect(seeded.bind).get_columns("users")}

    assert columns == {"id", "name", "email", "role", "client_id"}