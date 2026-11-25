import pytest
from fastapi import HTTPException

from shared.transitions import MACHINES, StateMachine

EXPECTED = {
    "ORDER": {
        "SUBMITTED": {"AWAITING_PAYMENT", "CANCELLED"},
        "AWAITING_PAYMENT": {"PAID", "CANCELLED"},
        "PAID": {"COMPLETED", "CANCELLED"},
        "COMPLETED": set(),
        "CANCELLED": set(),
    },
    "SUBSCRIPTION": {
        "PENDING": {"ACTIVE", "CANCELLED"},
        "ACTIVE": {"SUSPENDED", "TERMINATED"},
        "SUSPENDED": {"ACTIVE", "TERMINATED"},
        "TERMINATED": set(),
        "CANCELLED": set(),
    },
    "TICKET": {
        "OPEN": {"ASSIGNED", "CANCELLED"},
        "ASSIGNED": {"IN_PROGRESS", "OPEN", "CANCELLED"},
        "IN_PROGRESS": {"RESOLVED", "ASSIGNED"},
        "RESOLVED": {"CLOSED", "REOPENED"},
        "REOPENED": {"ASSIGNED", "IN_PROGRESS"},
        "CLOSED": set(),
        "CANCELLED": set(),
    },
    "INVOICE": {
        "DRAFT": {"ISSUED", "VOID"},
        "ISSUED": {"PARTIALLY_PAID", "PAID", "OVERDUE", "VOID"},
        "PARTIALLY_PAID": {"PAID", "OVERDUE", "VOID"},
        "OVERDUE": {"PAID", "PARTIALLY_PAID", "VOID"},
        "PAID": {"CREDITED"},
        "CREDITED": set(),
        "VOID": set(),
    },
    "STOCK_REQUEST": {
        "REQUESTED": {"READY_TO_ISSUE", "PENDING_STOCK", "CANCELLED"},
        "PENDING_STOCK": {"READY_TO_ISSUE", "CANCELLED"},
        "READY_TO_ISSUE": {"ISSUED", "CANCELLED"},
        "ISSUED": {"RETURNED"},
        "RETURNED": set(),
        "CANCELLED": set(),
    },
    "UNIT": {
        "IN_STOCK": {"RESERVED", "FAULTY"},
        "RESERVED": {"IN_STOCK", "WITH_TECHNICIAN"},
        "WITH_TECHNICIAN": {"INSTALLED", "RETURNED", "FAULTY", "LOST"},
        "INSTALLED": {"RETURNED", "LOST"},
        "RETURNED": {"IN_STOCK", "FAULTY"},
        "FAULTY": {"WRITTEN_OFF", "IN_STOCK"},
        "LOST": {"WRITTEN_OFF"},
        "WRITTEN_OFF": set(),
    },
}

ALL_PAIRS = [(name, cur, new) for name, table in EXPECTED.items() for cur, nxt in table.items() for new in nxt]


def test_machine_set_is_exact():
    assert set(MACHINES) == set(EXPECTED)


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_states_match(name):
    assert MACHINES[name].states == set(EXPECTED[name])


@pytest.mark.parametrize("name,current,new", ALL_PAIRS)
def test_listed_transitions_are_allowed(name, current, new):
    machine = MACHINES[name]
    assert machine.can(current, new)
    machine.assert_transition(current, new)


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_unlisted_transition_is_rejected_with_409(name):
    machine = MACHINES[name]
    states = sorted(machine.states)
    current, new = next(
        (c, n) for c in states for n in states if n not in EXPECTED[name][c]
    )
    assert not machine.can(current, new)
    with pytest.raises(HTTPException) as exc_info:
        machine.assert_transition(current, new)
    exc = exc_info.value
    assert exc.status_code == 409
    assert exc.detail["code"] == "INVALID_TRANSITION"
    assert exc.detail["message"] == f"{name}: {current} -> {new} tidak diizinkan"
    assert isinstance(exc.detail["details"], dict)


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_terminal_states_allow_nothing(name):
    machine = MACHINES[name]
    for state, allowed in EXPECTED[name].items():
        if not allowed:
            assert all(not machine.can(state, other) for other in machine.states)


def test_unknown_state_is_rejected():
    machine = StateMachine("X", {"A": {"B"}, "B": set()})
    assert not machine.can("Z", "A")
    with pytest.raises(HTTPException):
        machine.assert_transition("Z", "A")
