from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Text
from pgvector.sqlalchemy import Vector


class Base(DeclarativeBase):
    pass


class Procedure(Base):
    __tablename__ = "procedures"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    steps: Mapped[str] = mapped_column(Text)
    warnings: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list] = mapped_column(Vector(3072))