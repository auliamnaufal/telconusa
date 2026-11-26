from typing import Any

from fastapi import HTTPException


class StateMachine:
    def __init__(self, name: str, transitions: dict[str, set[str]]) -> None:
        self.name = name
        self.transitions = transitions
        self.states = frozenset(transitions)

    def can(self, current: str, new: str) -> bool:
        return new in self.transitions.get(current, set())

    def assert_transition(self, current: str, new: str) -> None:
        if self.can(current, new):
            return
        details: dict[str, Any] = {
            "machine": self.name,
            "current": current,
            "requested": new,
            "allowed": sorted(self.transitions.get(current, set())),
        }
        raise HTTPException(
            status_code=409,
            detail={
                "code": "INVALID_TRANSITION",
                "message": f"{self.name}: {current} -> {new} tidak diizinkan",
                "details": details,
            },
        )


MACHINES: dict[str, StateMachine] = {
    machine.name: machine
    for machine in (
        StateMachine(
            "ORDER",
            {
                "SUBMITTED": {"AWAITING_PAYMENT", "CANCELLED"},
                "AWAITING_PAYMENT": {"PAID", "CANCELLED"},
                "PAID": {"COMPLETED", "CANCELLED"},
                "COMPLETED": set(),
                "CANCELLED": set(),
            },
        ),
        StateMachine(
            "SUBSCRIPTION",
            {
                "PENDING": {"ACTIVE", "CANCELLED"},
                "ACTIVE": {"SUSPENDED", "TERMINATED"},
                "SUSPENDED": {"ACTIVE", "TERMINATED"},
                "TERMINATED": set(),
                "CANCELLED": set(),
            },
        ),
        StateMachine(
            "TICKET",
            {
                "OPEN": {"ASSIGNED", "CANCELLED"},
                "ASSIGNED": {"IN_PROGRESS", "OPEN", "CANCELLED"},
                "IN_PROGRESS": {"RESOLVED", "ASSIGNED"},
                "RESOLVED": {"CLOSED", "REOPENED"},
                "REOPENED": {"ASSIGNED", "IN_PROGRESS"},
                "CLOSED": set(),
                "CANCELLED": set(),
            },
        ),
        StateMachine(
            "INVOICE",
            {
                "DRAFT": {"ISSUED", "VOID"},
                "ISSUED": {"PARTIALLY_PAID", "PAID", "OVERDUE", "VOID"},
                "PARTIALLY_PAID": {"PAID", "OVERDUE", "VOID"},
                "OVERDUE": {"PAID", "PARTIALLY_PAID", "VOID"},
                "PAID": {"CREDITED"},
                "CREDITED": set(),
                "VOID": set(),
            },
        ),
        StateMachine(
            "STOCK_REQUEST",
            {
                "REQUESTED": {"READY_TO_ISSUE", "PENDING_STOCK", "CANCELLED"},
                "PENDING_STOCK": {"READY_TO_ISSUE", "CANCELLED"},
                "READY_TO_ISSUE": {"ISSUED", "CANCELLED"},
                "ISSUED": {"RETURNED"},
                "RETURNED": set(),
                "CANCELLED": set(),
            },
        ),
        StateMachine(
            "UNIT",
            {
                "IN_STOCK": {"RESERVED", "FAULTY"},
                "RESERVED": {"IN_STOCK", "WITH_TECHNICIAN"},
                "WITH_TECHNICIAN": {"INSTALLED", "RETURNED", "FAULTY", "LOST"},
                "INSTALLED": {"RETURNED", "LOST"},
                "RETURNED": {"IN_STOCK", "FAULTY"},
                "FAULTY": {"WRITTEN_OFF", "IN_STOCK"},
                "LOST": {"WRITTEN_OFF"},
                "WRITTEN_OFF": set(),
            },
        ),
    )
}
