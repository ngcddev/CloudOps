"""has_report persistido en security_checks (auditoría BD-03, spec 022 T19).

La lista de corridas de la puerta de seguridad cargaba el JSON de Trivy y del SBOM de cada control solo para decir si había reporte. Ahora es una columna booleana
y el reporte se carga solo cuando se pide (columna diferida).

Revisión: 0016
Anterior: 0015
"""
import sqlalchemy as sa
from alembic import op

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("security_checks", sa.Column("has_report", sa.Boolean(), nullable=False, server_default=sa.false()))
    # Un JSON «null» guardado (None de Python) no es un reporte: se compara el texto
    op.execute("UPDATE security_checks SET has_report = (report IS NOT NULL AND CAST(report AS TEXT) <> 'null')")


def downgrade() -> None:
    op.drop_column("security_checks", "has_report")
