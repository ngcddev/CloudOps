"""Crea reports: los reportes operativo y ejecutivo con los datos del mes congelados (spec 013).

Revisión: 0014
Anterior: 0013
"""
from alembic import op
import sqlalchemy as sa


revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.id"), nullable=True),
        sa.Column("month", sa.String(7), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("generated_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_reports_client_id", "reports", ["client_id"])


def downgrade() -> None:
    op.drop_index("ix_reports_client_id", table_name="reports")
    op.drop_table("reports")
