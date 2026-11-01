"""Crea los reportes mensuales operativo y ejecutivo (spec 013, T01).

`data` guarda los números del mes al generarse, para que el reporte no cambie después. No hay `pdf_path`:
el PDF lo produce el navegador (decisión 1 de specs/013-reportes/tasks.md).

Revisión: 0011
Anterior: 0010
"""
from alembic import op
import sqlalchemy as sa


revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=True),
        sa.Column("month", sa.String(length=7), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("generated_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.ForeignKeyConstraint(["generated_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reports_client_id", "reports", ["client_id"])


def downgrade() -> None:
    op.drop_index("ix_reports_client_id", table_name="reports")
    op.drop_table("reports")
