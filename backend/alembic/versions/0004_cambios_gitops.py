"""Crea change_requests y deployments, y suma versión y estado de sincronización a services (spec 005, T07).

Revisión: 0004
Anterior: 0003
"""
from alembic import op
import sqlalchemy as sa


revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "change_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticket_id", sa.Integer(), nullable=False),
        sa.Column("service_id", sa.Integer(), nullable=False),
        sa.Column("from_version", sa.String(length=50), nullable=False),
        sa.Column("to_version", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("requested_by_id", sa.Integer(), nullable=True),
        sa.Column("approved_by_id", sa.Integer(), nullable=True),
        sa.Column("gitops_commit_sha", sa.String(length=64), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deployed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"]),
        sa.ForeignKeyConstraint(["service_id"], ["services.id"]),
        sa.ForeignKeyConstraint(["requested_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["approved_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "deployments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("service_id", sa.Integer(), nullable=False),
        sa.Column("version", sa.String(length=50), nullable=False),
        sa.Column("commit_sha", sa.String(length=64), nullable=True),
        sa.Column("author", sa.String(length=200), nullable=False),
        sa.Column("source", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["service_id"], ["services.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    # Los servicios que ya existen quedan en v1 y con estado "Unknown" hasta que Argo CD informe.
    with op.batch_alter_table("services") as batch:
        batch.add_column(sa.Column("current_version", sa.String(length=50), nullable=False, server_default="v1"))
        batch.add_column(sa.Column("stable_version", sa.String(length=50), nullable=False, server_default="v1"))
        batch.add_column(sa.Column("sync_status", sa.String(length=30), nullable=False, server_default="Unknown"))
        batch.add_column(sa.Column("health_status", sa.String(length=30), nullable=False, server_default="Unknown"))


def downgrade() -> None:
    with op.batch_alter_table("services") as batch:
        batch.drop_column("health_status")
        batch.drop_column("sync_status")
        batch.drop_column("stable_version")
        batch.drop_column("current_version")
    op.drop_table("deployments")
    op.drop_table("change_requests")
