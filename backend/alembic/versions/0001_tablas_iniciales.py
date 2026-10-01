"""Migración inicial del Hub (spec 001, T04): agencias, planes, SLA, clientes, proyectos y servicios.

Revisión: 0001
Anterior: ninguna
"""
from alembic import op
import sqlalchemy as sa


revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("agencies",
    sa.Column("id", sa.Integer(), nullable=False),
    sa.Column("name", sa.String(length=200), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.PrimaryKeyConstraint("id")
    )
    op.create_table("plans",
    sa.Column("id", sa.Integer(), nullable=False),
    sa.Column("code", sa.String(length=50), nullable=False),
    sa.Column("name", sa.String(length=100), nullable=False),
    sa.Column("slo_availability", sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column("support_hours", sa.String(length=100), nullable=False),
    sa.Column("cpu_quota", sa.String(length=50), nullable=False),
    sa.Column("memory_quota", sa.String(length=50), nullable=False),
    sa.Column("monthly_price", sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column("included_hours", sa.Numeric(precision=8, scale=2), nullable=True),
    sa.PrimaryKeyConstraint("id"),
    sa.UniqueConstraint("code")
    )
    op.create_table("sla_policies",
    sa.Column("id", sa.Integer(), nullable=False),
    sa.Column("priority", sa.String(length=2), nullable=False),
    sa.Column("response_minutes", sa.Integer(), nullable=False),
    sa.Column("resolution_minutes", sa.Integer(), nullable=False),
    sa.Column("clock", sa.String(length=30), nullable=False),
    sa.PrimaryKeyConstraint("id"),
    sa.UniqueConstraint("priority")
    )
    op.create_table("clients",
    sa.Column("id", sa.Integer(), nullable=False),
    sa.Column("agency_id", sa.Integer(), nullable=True),
    sa.Column("name", sa.String(length=200), nullable=False),
    sa.Column("contact_name", sa.String(length=200), nullable=True),
    sa.Column("email", sa.String(length=200), nullable=True),
    sa.Column("phone", sa.String(length=50), nullable=True),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.ForeignKeyConstraint(["agency_id"], ["agencies.id"], ),
    sa.PrimaryKeyConstraint("id")
    )
    op.create_table("projects",
    sa.Column("id", sa.Integer(), nullable=False),
    sa.Column("client_id", sa.Integer(), nullable=False),
    sa.Column("name", sa.String(length=200), nullable=False),
    sa.Column("description", sa.Text(), nullable=True),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ),
    sa.PrimaryKeyConstraint("id")
    )
    op.create_table("services",
    sa.Column("id", sa.Integer(), nullable=False),
    sa.Column("project_id", sa.Integer(), nullable=False),
    sa.Column("plan_id", sa.Integer(), nullable=False),
    sa.Column("name", sa.String(length=200), nullable=False),
    sa.Column("host", sa.String(length=255), nullable=False),
    sa.Column("template", sa.String(length=30), nullable=False),
    sa.Column("namespace", sa.String(length=100), nullable=False),
    sa.Column("status", sa.String(length=30), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.ForeignKeyConstraint(["plan_id"], ["plans.id"], ),
    sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ),
    sa.PrimaryKeyConstraint("id"),
    sa.UniqueConstraint("host"),
    sa.UniqueConstraint("namespace")
    )


def downgrade() -> None:
    op.drop_table("services")
    op.drop_table("projects")
    op.drop_table("clients")
    op.drop_table("sla_policies")
    op.drop_table("plans")
    op.drop_table("agencies")
