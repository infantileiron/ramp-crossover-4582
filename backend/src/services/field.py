from fastapi import HTTPException

from src.config.database import connect
from src.services.audit import record


def route_or_error(db, route_code):
    route = db.execute('SELECT * FROM field_route WHERE code=%s', (route_code,)).fetchone()
    if route is None:
        raise HTTPException(404, '未找到路线')
    return route


def routes():
    with connect() as db:
        return db.execute('SELECT * FROM field_route ORDER BY code').fetchall()


def field_rows(db, route_code):
    return db.execute('SELECT code, sequence, period1, period2 FROM field_pair '
                      'WHERE route_code=%s ORDER BY sequence, code', (route_code,)).fetchall()


def pairs(route_code):
    with connect() as db:
        route_or_error(db, route_code)
        return field_rows(db, route_code)


def save_pair(route_code, code, data, actor):
    with connect() as db:
        route_or_error(db, route_code)
        pair = db.execute('''
            INSERT INTO field_pair (route_code, code, sequence, period1, period2) VALUES (%s,%s,%s,%s,%s)
            ON CONFLICT (route_code, code) DO UPDATE SET period1=excluded.period1, period2=excluded.period2, updated_at=now()
            WHERE field_pair.sequence=excluded.sequence
            RETURNING code, sequence, period1, period2
        ''', (route_code, code, data.sequence, data.period1, data.period2)).fetchone()
        if pair is None:
            raise HTTPException(409, '已有受试者的分配顺序不可变更，请按原顺序补录')
        record(db, actor, 'pair_saved', f'{route_code}/{code}', data.model_dump(mode='json'))
        return pair


def plans(route_code):
    with connect() as db:
        route_or_error(db, route_code)
        return db.execute('SELECT * FROM analysis_plan WHERE route_code=%s ORDER BY id DESC', (route_code,)).fetchall()


def create_plan(data, actor):
    with connect() as db:
        route_or_error(db, data.route_code)
        plan = db.execute('''
            INSERT INTO analysis_plan (route_code, edition, min_pairs, gap_limit, created_by) VALUES (%s,%s,%s,%s,%s)
            ON CONFLICT (route_code, edition) DO NOTHING RETURNING *
        ''', (data.route_code, data.edition, data.min_pairs, data.gap_limit, actor)).fetchone()
        if plan is None:
            raise HTTPException(409, '此路线已有同名版本')
        record(db, actor, 'plan_created', str(plan['id']), data.model_dump(mode='json'))
        return plan
