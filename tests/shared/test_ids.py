import pytest

from shared.ids import make_counter_model, next_code


@pytest.fixture
def setup(make_base, make_session_factory):
    Base = make_base()
    Counter = make_counter_model(Base)
    return Counter, make_session_factory(Base)


def test_next_code_is_sequential_and_formatted(setup):
    Counter, factory = setup
    with factory() as db:
        codes = [next_code(db, Counter, "ORDER:2026", "ORD-2026-{n:06d}") for _ in range(3)]
        db.commit()
    assert codes == ["ORD-2026-000001", "ORD-2026-000002", "ORD-2026-000003"]


def test_counters_are_independent_per_key(setup):
    Counter, factory = setup
    with factory() as db:
        assert next_code(db, Counter, "ORDER", "ORD-{n:03d}") == "ORD-001"
        assert next_code(db, Counter, "INVOICE", "INV-{n:03d}") == "INV-001"
        assert next_code(db, Counter, "ORDER", "ORD-{n:03d}") == "ORD-002"


def test_counter_persists_across_sessions(setup):
    Counter, factory = setup
    with factory() as db:
        next_code(db, Counter, "K", "X-{n}")
        db.commit()
    with factory() as db:
        assert next_code(db, Counter, "K", "X-{n}") == "X-2"
        db.commit()
        assert db.query(Counter).filter(Counter.key == "K").one().value == 2


def test_uncommitted_increment_is_rolled_back_with_caller(setup):
    Counter, factory = setup
    with factory() as db:
        next_code(db, Counter, "K", "X-{n}")
        db.rollback()
        assert next_code(db, Counter, "K", "X-{n}") == "X-1"
