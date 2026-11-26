import uuid
from sqlalchemy import Column, DateTime, String, func

from shared.event_receiver import make_processed_event_model
from shared.ids import make_counter_model
from shared.outbox import make_outbox_models

from app.database import Base

Counter = make_counter_model(Base)
OutboxEvent, DeadLetterEvent = make_outbox_models(Base)
ProcessedEvent = make_processed_event_model(Base)


def gen_uuid() -> str:
    return str(uuid.uuid4())


class Example(Base):
    """Contoh entity; ganti atau hapus sesuai domain modul."""

    __tablename__ = "examples"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(120), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
