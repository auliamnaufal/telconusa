"""Pekerjaan berkala (mis. kedaluwarsa reservasi, ulang cek anggaran).

Daftarkan fungsi sinkron `fn(db)` dengan `@job("nama", interval_seconds=60)` di modul slice
(diimpor dari `app/<slice>/__init__.py`). `relay_lifespan` (core/outbox.py) menjalankan semua
pekerjaan terdaftar di latar belakang; setiap putaran memakai sesi sendiri dan commit di akhir.
"""
import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Callable

from sqlalchemy.orm import Session

logger = logging.getLogger("telconusa.scm.jobs")


@dataclass(frozen=True)
class Job:
    name: str
    interval_seconds: float
    fn: Callable[[Session], Any]


JOBS: dict[str, Job] = {}


def job(name: str, interval_seconds: float = 60.0) -> Callable[[Callable[[Session], Any]], Callable[[Session], Any]]:
    def _register(fn: Callable[[Session], Any]) -> Callable[[Session], Any]:
        if name in JOBS:
            raise RuntimeError(f"Pekerjaan {name} sudah terdaftar")
        JOBS[name] = Job(name, interval_seconds, fn)
        return fn

    return _register


def run_job_once(job_or_name: Job | str, session_factory: Callable[[], Session]) -> Any:
    """Jalankan satu putaran: sesi baru, commit bila berhasil, rollback bila gagal (galat dilempar ulang)."""
    target = JOBS[job_or_name] if isinstance(job_or_name, str) else job_or_name
    db = session_factory()
    try:
        result = target.fn(db)
        db.commit()
        return result
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


async def run_job_loop(target: Job, session_factory: Callable[[], Session]) -> None:
    while True:
        try:
            await asyncio.to_thread(run_job_once, target, session_factory)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Pekerjaan %s gagal pada satu putaran", target.name)
        await asyncio.sleep(target.interval_seconds)
