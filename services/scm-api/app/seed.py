from sqlalchemy.orm import Session

from app.assets.seed import seed_assets
from app.catalog.seed import seed_catalog
from app.core.seed import seed_core
from app.database import SessionLocal


def seed_all(db: Session) -> None:
    """Seed semua slice berurutan (core dulu); aman dijalankan berulang."""
    seed_core(db)
    seed_assets(db)
    seed_catalog(db)


def main() -> None:
    db = SessionLocal()
    try:
        seed_all(db)
        db.commit()
        print("[scm-api] Seed completed successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
