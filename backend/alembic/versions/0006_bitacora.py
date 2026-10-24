"""Crea la bitácora audit_logs, de solo inserción (spec 007, T07).

En PostgreSQL un trigger rechaza UPDATE y DELETE, así la bitácora no se puede alterar ni desde
la aplicación ni con un descuido en SQL. SQLite (pruebas) no lo necesita.

Revisión: 0006
Anterior: 0005
"""
from alembic import op
import sqlalchemy as sa


revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("entity", sa.String(length=50), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("ip", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])
    op.create_index("ix_audit_logs_entity", "audit_logs", ["entity", "entity_id"])
    if op.get_bind().dialect.name == "postgresql":
        op.execute(
            """
            CREATE FUNCTION audit_logs_solo_insercion() RETURNS trigger AS $$
            BEGIN
                RAISE EXCEPTION 'La bitácora es de solo inserción: no se puede editar ni borrar.';
            END;
            $$ LANGUAGE plpgsql
            """
        )
        op.execute(
            """
            CREATE TRIGGER audit_logs_inmutable
            BEFORE UPDATE OR DELETE ON audit_logs
            FOR EACH ROW EXECUTE FUNCTION audit_logs_solo_insercion()
            """
        )


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP TRIGGER IF EXISTS audit_logs_inmutable ON audit_logs")
        op.execute("DROP FUNCTION IF EXISTS audit_logs_solo_insercion()")
    op.drop_index("ix_audit_logs_entity", table_name="audit_logs")
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_table("audit_logs")
