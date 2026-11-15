"""Índices de las claves foráneas y dos restricciones únicas (auditoría BD-01 y BD-02, spec 022 T06).

Los índices aceleran las consultas de tickets, eventos, horas, cambios y despliegues, que PostgreSQL no indexa solo por tener una clave foránea.
Los dos únicos pasan a la base lo que el código solo comprobaba con un SELECT: un solo cambio en curso por servicio y un solo control por corrida,
paso e imagen. Si la base ya tiene duplicados, la migración se detiene con un mensaje que dice cuáles, en vez de corregirlos sin avisar.

Revisión: 0015
Anterior: 0014
"""
from alembic import op
import sqlalchemy as sa


revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None

# Mismos estados que app.models.change_request.OPEN_STATUSES (una prueba comprueba que coinciden)
ABIERTOS = "status IN ('pendiente', 'aprobada', 'en_validacion')"

INDICES = [
    ("ix_tickets_service_id", "tickets", ["service_id"]),
    ("ix_tickets_created_at", "tickets", ["created_at"]),
    ("ix_ticket_events_ticket_id", "ticket_events", ["ticket_id"]),
    ("ix_work_logs_ticket_id", "work_logs", ["ticket_id"]),
    ("ix_work_logs_user_id", "work_logs", ["user_id"]),
    ("ix_change_requests_service_status", "change_requests", ["service_id", "status"]),
    ("ix_change_requests_ticket_id", "change_requests", ["ticket_id"]),
    ("ix_deployments_service_id_id", "deployments", ["service_id", "id"]),
    ("ix_services_project_id", "services", ["project_id"]),
    ("ix_projects_client_id", "projects", ["client_id"]),
    ("ix_users_client_id", "users", ["client_id"]),
]


def _comprobar_sin_duplicados() -> None:
    """Un índice único no se puede crear sobre datos que ya lo violan: se dice cuáles son para corregirlos a mano."""
    conexion = op.get_bind()
    cambios = conexion.execute(sa.text(
        f"SELECT service_id, COUNT(*) FROM change_requests WHERE {ABIERTOS} GROUP BY service_id HAVING COUNT(*) > 1"
    )).fetchall()
    controles = conexion.execute(sa.text(
        "SELECT run_id, step, COALESCE(image, ''), COUNT(*) FROM security_checks GROUP BY run_id, step, COALESCE(image, '') HAVING COUNT(*) > 1"
    )).fetchall()
    if not cambios and not controles:
        return
    detalle = []
    if cambios:
        detalle.append("servicios con más de un cambio abierto (service_id, cantidad): " + ", ".join(f"({c[0]}, {c[1]})" for c in cambios))
    if controles:
        detalle.append("controles repetidos (run_id, paso, imagen, cantidad): " + ", ".join(f"({c[0]}, {c[1]}, '{c[2]}', {c[3]})" for c in controles))
    raise RuntimeError(
        "No se puede crear el índice único porque la base ya tiene duplicados. Cierre o borre los sobrantes y vuelva a migrar. " + "; ".join(detalle)
    )


def upgrade() -> None:
    _comprobar_sin_duplicados()
    for nombre, tabla, columnas in INDICES:
        op.create_index(nombre, tabla, columnas)
    op.create_index(
        "uq_change_requests_open_per_service", "change_requests", ["service_id"], unique=True,
        postgresql_where=sa.text(ABIERTOS), sqlite_where=sa.text(ABIERTOS),
    )
    op.create_index(
        "uq_security_checks_run_step_image", "security_checks", ["run_id", "step", sa.text("coalesce(image, '')")], unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_security_checks_run_step_image", table_name="security_checks")
    op.drop_index("uq_change_requests_open_per_service", table_name="change_requests")
    for nombre, tabla, _ in reversed(INDICES):
        op.drop_index(nombre, table_name=tabla)
