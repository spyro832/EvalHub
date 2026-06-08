from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid


class Benchmark(Base, TimestampMixin):
    __tablename__ = "benchmarks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    author: Mapped[str | None] = mapped_column(String(200), nullable=True)

    items: Mapped[list["BenchmarkItem"]] = relationship(
        "BenchmarkItem", back_populates="benchmark", lazy="selectin", cascade="all, delete-orphan"
    )


class BenchmarkItem(Base, TimestampMixin):
    __tablename__ = "benchmark_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    benchmark_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("benchmarks.id", ondelete="CASCADE"), nullable=False
    )
    input: Mapped[str] = mapped_column(Text, nullable=False)
    expected_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_tags: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Arbitrary metadata (difficulty, language, topic, etc.)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    benchmark: Mapped["Benchmark"] = relationship("Benchmark", back_populates="items")
