from datetime import date
from sqlalchemy.orm import Session
from app.models import FiscalPeriod, JournalEntry, JournalLine


def post_journal(
    db: Session,
    *,
    entry_date: date,
    source_type: str,
    source_id: str,
    rule_code: str,
    description: str,
    lines: list[tuple[str, int, int]],
    business_line: str | None = None,
) -> JournalEntry:
    """Double-entry posting engine (NFR-01: total debit MUST equal total credit)."""
    total_debit = sum(d for _, d, _ in lines)
    total_credit = sum(c for _, _, c in lines)
    if total_debit <= 0 or total_debit != total_credit:
        raise ValueError(f"Unbalanced journal rejected: debit={total_debit}, credit={total_credit}")

    period_code = entry_date.strftime("%Y-%m")
    period = db.query(FiscalPeriod).filter_by(period_code=period_code).first()
    if period and period.status == "LOCKED":
        raise ValueError(f"Fiscal period {period_code} is LOCKED")

    # Idempotency check per (source_type, source_id, rule_code)
    existing = (
        db.query(JournalEntry)
        .filter_by(source_type=source_type, source_id=source_id, rule_code=rule_code)
        .first()
    )
    if existing:
        return existing

    seq = db.query(JournalEntry).count() + 1
    entry = JournalEntry(
        journal_no=f"JE-{seq:06d}",
        entry_date=entry_date,
        period_code=period_code,
        source_type=source_type,
        source_id=source_id,
        rule_code=rule_code,
        description=description,
        status="POSTED",
    )
    db.add(entry)
    db.flush()

    for acc_code, debit, credit in lines:
        db.add(JournalLine(
            journal_entry_id=entry.id,
            account_code=acc_code,
            debit=debit,
            credit=credit,
            business_line=business_line,
        ))
    return entry
