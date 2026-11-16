"""Esquema afinado: jsonb, fechas obligatorias y correo único sin distinguir mayúsculas (auditoría BD-04, BD-05 y BD-07, spec 022 T34).

- BD-04: las columnas de documentos pasan de `json` (texto que se vuelve a analizar en cada lectura) a `jsonb`, solo en PostgreSQL.
- BD-05: las fechas de creación que los modelos tipan como obligatorias pero la base dejaba `NULL`-ables pasan a `NOT NULL` (lo que hubiera `NULL` se rellena con la hora de la migración), solo en PostgreSQL.
- BD-07: índice único sobre `lower(email)`: `Ana@x.com` y `ana@x.com` ya no pueden coexistir y el login (que busca con `lower`) puede usar un índice. Si ya hay correos que solo
  se distinguen por mayúsculas, la migración se detiene y dice cuáles, en vez de elegir uno.

Revisión: 0017
Anterior: 0016
"""
import sqlalchemy as sa
from alembic import op

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None

COLUMNAS_JSON = [
    ("ai_drafts", "checks"),
    ("ai_queries", "context_sections"),
    ("audit_logs", "details"),
    ("kb_chunks", "embedding"),
    ("reports", "data"),
    ("security_checks", "report"),
    ("security_runs", "images"),
    ("security_runs", "image_digests"),
]
FECHAS = [
    ("audit_logs", "created_at"),
    ("security_runs", "started_at"),
    ("security_checks", "created_at"),
    ("incidents", "created_at"),
    ("incident_events", "created_at"),
    ("ai_queries", "created_at"),
    ("ai_drafts", "created_at"),
    ("kb_documents", "indexed_at"),
    ("reports", "created_at"),
]


def _es_postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    repetidos = op.get_bind().execute(sa.text("SELECT lower(email), count(*) FROM users GROUP BY lower(email) HAVING count(*) > 1")).fetchall()
    if repetidos:
        detalle = ", ".join(f"{correo} ({cantidad})" for correo, cantidad in repetidos)
        raise RuntimeError(f"Hay correos que solo se distinguen por mayúsculas: {detalle}. Corrígelos a mano antes de migrar (BD-07).")
    op.execute("UPDATE users SET email = lower(email) WHERE email <> lower(email)")
    op.create_index("uq_users_email_lower", "users", [sa.text("lower(email)")], unique=True)

    if _es_postgres():
        for tabla, columna in COLUMNAS_JSON:
            op.execute(f'ALTER TABLE {tabla} ALTER COLUMN "{columna}" TYPE jsonb USING "{columna}"::jsonb')
        for tabla, columna in FECHAS:
            op.execute(f'UPDATE {tabla} SET "{columna}" = now() WHERE "{columna}" IS NULL')
            op.execute(f'ALTER TABLE {tabla} ALTER COLUMN "{columna}" SET NOT NULL')


def downgrade() -> None:
    if _es_postgres():
        for tabla, columna in FECHAS:
            op.execute(f'ALTER TABLE {tabla} ALTER COLUMN "{columna}" DROP NOT NULL')
        for tabla, columna in COLUMNAS_JSON:
            op.execute(f'ALTER TABLE {tabla} ALTER COLUMN "{columna}" TYPE json USING "{columna}"::json')
    op.drop_index("uq_users_email_lower", table_name="users")
