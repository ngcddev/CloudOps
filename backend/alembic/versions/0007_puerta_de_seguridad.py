"""Crea las corridas y los controles de la puerta de seguridad (spec 006, T12).

Revisión: 0007
Anterior: 0006
"""
from alembic import op
import sqlalchemy as sa


revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "security_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("service_id", sa.Integer(), nullable=False),
        sa.Column("version", sa.String(length=50), nullable=False),
        sa.Column("commit_sha", sa.String(length=64), nullable=True),
        sa.Column("images", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("failed_step", sa.String(length=30), nullable=True),
        sa.Column("image_digests", sa.JSON(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["service_id"], ["services.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_security_runs_service_version", "security_runs", ["service_id", "version"])
    op.create_table(
        "security_checks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("step", sa.String(length=30), nullable=False),
        sa.Column("image", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=10), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("report", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["security_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_security_checks_run", "security_checks", ["run_id"])


def downgrade() -> None:
    op.drop_index("ix_security_checks_run", table_name="security_checks")
    op.drop_table("security_checks")
    op.drop_index("ix_security_runs_service_version", table_name="security_runs")
    op.drop_table("security_runs")
