"""Mesin status SCM.

`STOCK_REQUEST` dan `UNIT` berasal dari `shared.transitions` (area bersama, jangan diubah).
Mesin PR, PO, dan GR dimiliki SCM dan dibuat di sini dengan kelas `StateMachine` yang sama.
Transisi tidak sah menjawab `409 INVALID_TRANSITION` lewat `assert_transition`.
"""
from shared.transitions import MACHINES, StateMachine

STOCK_REQUEST: StateMachine = MACHINES["STOCK_REQUEST"]
UNIT: StateMachine = MACHINES["UNIT"]

PURCHASE_REQUEST = StateMachine(
    "PURCHASE_REQUEST",
    {
        "PENDING_BUDGET": {"BUDGET_OK", "BUDGET_REJECTED", "CANCELLED"},
        "BUDGET_REJECTED": {"PENDING_BUDGET", "CANCELLED"},
        "BUDGET_OK": {"PO_CREATED", "CANCELLED"},
        "PO_CREATED": set(),
        "CANCELLED": set(),
    },
)

PURCHASE_ORDER = StateMachine(
    "PURCHASE_ORDER",
    {
        "DRAFT": {"PENDING_APPROVAL", "CANCELLED"},
        "PENDING_APPROVAL": {"APPROVED", "REJECTED", "CANCELLED"},
        "APPROVED": {"PARTIALLY_RECEIVED", "RECEIVED", "CANCELLED"},
        "PARTIALLY_RECEIVED": {"RECEIVED"},
        "RECEIVED": {"CLOSED"},
        "CLOSED": set(),
        "REJECTED": set(),
        "CANCELLED": set(),
    },
)

GOODS_RECEIPT = StateMachine("GOODS_RECEIPT", {"POSTED": set()})
