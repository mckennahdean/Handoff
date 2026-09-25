from datetime import datetime, timezone

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Text, DateTime, Float, Integer, ForeignKey

from pgvector.sqlalchemy import Vector
from typing import Optional


class Base(DeclarativeBase):
    pass

class ProcedureChunk(Base):
    """One retrieval chunk per procedure step or warning.

    Retrieval matches questions against these chunks instead of one
    whole-procedure embedding, which diluted meaning (see the
    evaluation in evaluation/run_retrieval.py, Strategy C).
    """
    __tablename__ = "procedure_chunks"

    id: Mapped[int] = mapped_column(primary_key=True)

    # CASCADE: deleting a procedure deletes its chunks in the database.
    procedure_id: Mapped[int] = mapped_column(
        ForeignKey("procedures.id", ondelete="CASCADE"),
        index=True
    )

    text: Mapped[str] = mapped_column(
        Text
    )

    embedding: Mapped[list] = mapped_column(
        Vector(3072)
    )

class Procedure(Base):
    __tablename__ = "procedures"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(
        String(200)
    )

    steps: Mapped[str] = mapped_column(
        Text
    )

    warnings: Mapped[str] = mapped_column(
        Text
    )

    # Nullable because pending drafts have no embedding yet.
    # The embedding is generated only when the owner approves.
    embedding: Mapped[Optional[list]] = mapped_column(
        Vector(3072),
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="pending"
    )

    version: Mapped[int] = mapped_column(
        Integer,
        default=1
    )

    last_confirmed: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    capture_method: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True
    )

    # JSON list of the AI's follow-up questions, kept as a
    # record of what the owner was asked before approval.
    gap_questions: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )


class Gap(Base):
    __tablename__ = "gaps"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    question: Mapped[str] = mapped_column(
        Text
    )

    # Closest similarity any procedure reached for this question.
    similarity: Mapped[float] = mapped_column(
        Float
    )

    frequency_count: Mapped[int] = mapped_column(
        Integer,
        default=1
    )

    # Embedding of the question, used to group same-meaning
    # questions and to detect when a new procedure answers it.
    embedding: Mapped[Optional[list]] = mapped_column(
        Vector(3072),
        nullable=True
    )

    # open, resolved (a procedure now covers it), or dismissed.
    status: Mapped[str] = mapped_column(
        String(20),
        default="open"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    last_asked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    resolved_by_procedure_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )

    # JSON list of other wordings grouped into this gap, so a
    # mistaken grouping never hides a question from the owner.
    variants: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String(100)
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True
    )

    password_hash: Mapped[str] = mapped_column(
        String(255)
    )

    role: Mapped[str] = mapped_column(
        String(20)
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

class Business(Base):
    __tablename__ = "business"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String(200)
    )

    invite_code: Mapped[str] = mapped_column(
        String(20),
        unique=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )