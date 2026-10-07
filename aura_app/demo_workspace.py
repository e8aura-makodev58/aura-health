"""Synthetic development data lifecycle, outside patient/domain policy.

Seed privately, validate completion, then publish atomically. Never repair a partial
or unknown database by deleting patient records. Reset archives the entire synthetic
workspace and installs a copy of the already-verified baseline.
"""

from contextlib import contextmanager
import fcntl
import os
from pathlib import Path
import shutil
import sqlite3
from tempfile import TemporaryDirectory
from uuid import uuid4

from .persistence import SQLiteRepositoryFactory


def expected(seed):
    from .demo import CHECKPOINTS
    return {f"demo-{key}-{seed}": f"demo-{key}-{seed}-{day}-{'safety-text' if key == 'F' else 'checkin'}"
            for key, _label, _case, day, _explain in CHECKPOINTS}


def verify(path, seed=7, *, exclusive=False):
    path = Path(path)
    with sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True) as conn:
        patients = {row[0] for row in conn.execute("SELECT patient_id FROM patients")}
        for patient, event in expected(seed).items():
            if conn.execute("SELECT 1 FROM app_events WHERE patient_id=? AND event_id=?", (patient, event)).fetchone() is None:
                raise ValueError("Incomplete synthetic seed. Preserve this database and use a fresh explicit path.")
        if exclusive and patients != set(expected(seed)):
            raise ValueError("Reset refused: database contains profiles outside the synthetic catalog")


@contextmanager
def seed_lock(path):
    with Path(str(path) + ".seed.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield


def prepare_snapshot(path, seed, builder):
    path = Path(path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with seed_lock(path):
        if path.exists():
            verify(path, seed)
        else:
            with TemporaryDirectory(prefix="aura-seed-", dir=path.parent) as temporary:
                staged = Path(temporary) / "complete.sqlite3"
                builder(staged, seed)
                verify(staged, seed, exclusive=True)
                os.replace(staged, path)
    return SQLiteRepositoryFactory(path)


def reset_snapshot(path, baseline, seed=7):
    """Operator-only local reset, with a recoverable archive; server must be stopped."""
    path, baseline = Path(path).resolve(), Path(baseline).resolve()
    if path == baseline or path.suffix != ".sqlite3" or not path.is_file():
        raise ValueError("Reset requires distinct explicit .sqlite3 workspace and baseline files")
    verify(path, seed, exclusive=True)
    verify(baseline, seed, exclusive=True)
    with seed_lock(path), TemporaryDirectory(prefix="aura-reset-", dir=path.parent) as temporary:
        replacement = Path(temporary) / "replacement.sqlite3"
        shutil.copyfile(baseline, replacement)
        archive = path.with_name(path.name + f".archive-{uuid4().hex}")
        shutil.copyfile(path, archive)
        os.replace(replacement, path)
    return archive
