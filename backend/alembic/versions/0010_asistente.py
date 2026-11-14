"""Crea ai_queries: cada pregunta al asistente y la decisión de la compuerta (spec 012).

Revisión: 0010
Anterior: 0009
"""
from alembic import op
import sqlalchemy as sa


revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_queries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("gate_label", sa.String(length=20), nullable=False),
        sa.Column("p_fuera_de_tema", sa.Float(), nullable=False),
        sa.Column("gate_version", sa.String(length=30), nullable=False),
        sa.Column("llm_woken", sa.Boolean(), nullable=False),
        sa.Column("model", sa.String(length=60), nullable=True),
        sa.Column("prompt_version", sa.String(length=30), nullable=True),
        sa.Column("llm_ok", sa.Boolean(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("feedback_label", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_queries_created_at", "ai_queries", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_ai_queries_created_at", table_name="ai_queries")
    op.drop_table("ai_queries")
