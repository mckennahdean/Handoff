from datetime import datetime, timezone

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Text, DateTime, Float, Integer

from pgvector.sqlalchemy import Vector
from typing import Optional


class Base(DeclarativeBase):
    pass


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
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    capture_method: Mapped[Optional[str]] = mapped_column(
        String(20),
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

    similarity: Mapped[float] = mapped_column(
        Float
    )

    frequency_count: Mapped[int] = mapped_column(
        Integer,
        default=1
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
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
        DateTime,
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
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )