from pathlib import Path

from src.config.database import connect

with connect() as db:
    db.execute("SELECT pg_advisory_xact_lock(5215)")
    for migration in sorted(Path("migrations").glob("*.sql")):
        db.execute(migration.read_text())
