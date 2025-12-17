from datetime import datetime
from sqlalchemy import Integer, Float, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

class SensorData(Base):
    __tablename__ = "sensor_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(10), nullable=False)
    hum: Mapped[float | None] = mapped_column(Float, nullable=True)
    bmp_press: Mapped[float | None] = mapped_column(Float, nullable=True)
    mq5: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mq3: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fused_temp: Mapped[float | None] = mapped_column(Float, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
