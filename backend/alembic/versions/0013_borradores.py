"""Crea ai_drafts: los borradores del asistente para un incidente, con su estado, su fuente y sus verificaciones (spec 012).

Revisión: 0013
Anterior: 0012
"""
from alembic import op
import sqlalchemy as sa


revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_drafts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("incident_id", sa.Integer(), sa.ForeignKey("incidents.id"), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="borrador_ia"),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("model", sa.String(60), nullable=True),
        sa.Column("prompt_version", sa.String(30), nullable=True),
        sa.Column("generated_text", sa.Text(), nullable=False),
        sa.Column("final_text", sa.Text(), nullable=True),
        sa.Column("checks", sa.JSON(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("approved_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_ai_drafts_incident_id", "ai_drafts", ["incident_id"])


def downgrade() -> None:
    op.drop_index("ix_ai_drafts_incident_id", table_name="ai_drafts")
    op.drop_table("ai_drafts")
