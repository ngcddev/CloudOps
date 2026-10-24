# Pruebas del modelo, migración y semilla de usuarios de la spec 004.
from sqlalchemy import inspect, text


def test_seed_carga_dos_usuarios_de_agencia_y_tres_de_clientes(seeded):
    users = seeded.execute(text("SELECT name, email, role, client_id FROM users ORDER BY id")).mappings().all()

    assert len(users) == 5
    assert sum(user["role"] == "agencia" for user in users) == 2
    assert sum(user["role"] == "cliente" for user in users) == 3
    assert sum(user["client_id"] is None for user in users) == 2
    assert all("password" not in user for user in users)


def test_seed_guarda_solo_el_hash_de_la_contrasena_de_desarrollo(seeded):
    from app.config import settings
    from app.services.auth import verify_password

    rows = seeded.execute(text("SELECT password_hash FROM users")).scalars().all()

    assert len(rows) == 5
    assert all(row.startswith("$2b$") for row in rows)
    assert all(settings.seed_user_password not in row for row in rows)
    assert all(verify_password(settings.seed_user_password, row) for row in rows)


def test_tabla_users_tiene_la_estructura_de_t02(seeded):
    columns = {column["name"] for column in inspect(seeded.bind).get_columns("users")}

    assert columns == {
        "id", "name", "email", "role", "client_id", "password_hash", "is_active", "last_login_at",
    }

def test_seed_passwords_da_contrasena_solo_a_quien_no_tiene(seeded):
    from app.models import User
    from app.seed import seed_passwords
    from app.services.auth import verify_password
    from sqlalchemy import select

    sofia = seeded.scalar(select(User).where(User.email == "sofia@forjadigital.test"))
    marta = seeded.scalar(select(User).where(User.email == "contacto@lasazon.test"))
    sofia.password_hash = None
    marta.password_hash = "hash-propio-de-marta"
    seeded.commit()

    assert seed_passwords(seeded) == 1

    seeded.refresh(sofia)
    seeded.refresh(marta)
    assert verify_password("clave-de-desarrollo", sofia.password_hash)
    assert marta.password_hash == "hash-propio-de-marta"
    assert seed_passwords(seeded) == 0
