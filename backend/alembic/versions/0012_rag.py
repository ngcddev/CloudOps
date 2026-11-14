"""Crea la base de conocimiento del RAG (kb_documents, kb_chunks) y anota en ai_queries cómo se eligió el contexto (spec 012).

Revisión: 0012
Anterior: 0011
"""
from alembic import op
import sqlalchemy as sa


revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "kb_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source", sa.String(120), nullable=False, unique=True),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("embedding_model", sa.String(80), nullable=False),
        sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("indexed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "kb_chunks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("kb_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("section", sa.String(200), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("embedding", sa.JSON(), nullable=False),
        sa.UniqueConstraint("document_id", "position", name="uq_kb_chunks_document_position"),
    )
    with op.batch_alter_table("ai_queries") as batch:
        # completo | recuperacion | rag: cómo se armó realmente el contexto de esa respuesta (el RAG puede caer a léxico)
        batch.add_column(sa.Column("context_mode", sa.String(20), nullable=True))
        # Similitud coseno del mejor trozo (solo cuando se usó el RAG)
        batch.add_column(sa.Column("retrieval_score", sa.Float(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("ai_queries") as batch:
        batch.drop_column("retrieval_score")
        batch.drop_column("context_mode")
    op.drop_table("kb_chunks")
    op.drop_table("kb_documents")
