"""Suma a incidents las columnas del rollback (spec 009, T01).

Todas son nulas hasta que alguien pide el rollback. Los tipos de evento nuevos (`rollback_enviado`,
`rollback_confirmado` y `mensaje_cliente`) caben en `incident_events.type` (20 caracteres), así que no
hay tablas ni cambios de esquema adicionales.

Revisión: 0009
Anterior: 0008
"""
from alembic import op
import sqlalchemy as sa


revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("incidents") as batch:
        batch.add_column(sa.Column("rollback_from_version", sa.String(length=50), nullable=True))
        batch.add_column(sa.Column("rollback_to_version", sa.String(length=50), nullable=True))
        batch.add_column(sa.Column("rollback_commit_sha", sa.String(length=64), nullable=True))
        batch.add_column(sa.Column("rollback_by_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("rollback_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("rollback_confirmed_at", sa.DateTime(timezone=True), nullable=True))
        batch.create_foreign_key("fk_incidents_rollback_by", "users", ["rollback_by_id"], ["id"])


def downgrade() -> None:
    with op.batch_alter_table("incidents") as batch:
        batch.drop_constraint("fk_incidents_rollback_by", type_="foreignkey")
        batch.drop_column("rollback_confirmed_at")
        batch.drop_column("rollback_at")
        batch.drop_column("rollback_by_id")
        batch.drop_column("rollback_commit_sha")
        batch.drop_column("rollback_to_version")
        batch.drop_column("rollback_from_version")
