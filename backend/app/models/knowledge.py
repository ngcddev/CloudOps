# Base de conocimiento del asistente para el RAG (spec 012): documentos fuente y sus trozos con el embedding de cada uno.
# El índice vectorial es esta tabla: el vector va como lista de números (JSON, igual en PostgreSQL y SQLite) y la
# búsqueda calcula la similitud coseno en Python; con unas decenas de trozos no hace falta una extensión como pgvector.
# Solo contiene documentos del proyecto (la ayuda del Hub), nunca datos de clientes (principio 2).
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import JSON_DOC, Base


class KbDocument(Base):
    __tablename__ = "kb_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Nombre del archivo fuente (por ejemplo ayuda_hub.md)
    source: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    # SHA-256 del contenido: si cambia, el índice está vencido y se vuelve a generar
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    # Con qué modelo se calcularon los embeddings; si cambia el modelo, también hay que reindexar
    embedding_model: Mapped[str] = mapped_column(String(80), nullable=False)
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    indexed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    chunks: Mapped[list["KbChunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class KbChunk(Base):
    __tablename__ = "kb_chunks"
    __table_args__ = (UniqueConstraint("document_id", "position", name="uq_kb_chunks_document_position"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("kb_documents.id", ondelete="CASCADE"), nullable=False)
    # Título de la sección de la ayuda a la que pertenece el trozo (es lo que se cita como fuente)
    section: Mapped[str] = mapped_column(String(200), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    # Vector de la sección (768 números con nomic-embed-text)
    embedding: Mapped[list] = mapped_column(JSON_DOC, nullable=False)

    document: Mapped[KbDocument] = relationship(back_populates="chunks")
