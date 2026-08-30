from datetime import datetime

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Text, DateTime

from pgvector.sqlalchemy import Vector


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

    embedding: Mapped[list] = mapped_column(
        Vector(3072)
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="approved"
    )

    last_confirmed: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )


class Gap(Base):
    __tablename__ = "gaps"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    question: Mapped[str] = mapped_column(
        Text
    )

    similarity: Mapped[str] = mapped_column(
        String(50)
    )