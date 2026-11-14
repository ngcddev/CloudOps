"""Suma a ai_queries las secciones de ayuda que fundamentaron cada respuesta (spec 012).

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
    with op.batch_alter_table("ai_queries") as batch:
        batch.add_column(sa.Column("context_sections", sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("ai_queries") as batch:
        batch.drop_column("context_sections")
