from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, Session, mapped_column


def make_counter_model(Base: type) -> type:
    class IdCounter(Base):
        __tablename__ = "id_counters"

        key: Mapped[str] = mapped_column(String(64), primary_key=True)
        value: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)

    return IdCounter


def next_code(db: Session, Counter: type, key: str, template: str) -> str:
    """Increment the counter row inside the caller's transaction and format the new value.

    The row is locked with SELECT ... FOR UPDATE so concurrent requests get distinct numbers.
    A missing row is created on first use; commit stays with the caller.
    """
    counter = db.query(Counter).filter(Counter.key == key).with_for_update().first()
    if counter is None:
        counter = Counter(key=key, value=0)
        db.add(counter)
    counter.value += 1
    db.flush()
    return template.format(n=counter.value)
