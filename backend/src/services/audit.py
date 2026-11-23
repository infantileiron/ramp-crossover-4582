from psycopg.types.json import Jsonb


def record(db, actor, event, entity, detail):
    db.execute('INSERT INTO audit_event (actor, event, entity, detail) VALUES (%s,%s,%s,%s)',
               (actor, event, entity, Jsonb(detail)))
