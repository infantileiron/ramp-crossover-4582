import logging

from fastapi import HTTPException
from psycopg.types.json import Jsonb
from redis.exceptions import RedisError

from src.config.database import connect, queue
from src.constants.domain import Role, RunState
from src.models.record import Pair
from src.services.audit import record
from src.services.crossover import METHOD
from src.services.field import field_rows, route_or_error
from src.utils.serial import fingerprint

WAKE_KEY = 'ramp:recalculate'
LOGGER = logging.getLogger(__name__)


def create_run(plan_id, actor):
    with connect() as db:
        plan = db.execute('SELECT * FROM analysis_plan WHERE id=%s', (plan_id,)).fetchone()
        if plan is None:
            raise HTTPException(404, '未找到参数版本')
        route = route_or_error(db, plan['route_code'])
        snapshot = {
            'method': METHOD,
            'route': route,
            'plan': {'id': plan_id, 'edition': plan['edition'], 'min_pairs': plan['min_pairs'], 'gap_limit': format(plan['gap_limit'], '.2f')},
            'pairs': [Pair(**row).snapshot() for row in field_rows(db, route['code'])],
        }
        digest = fingerprint(snapshot)
        report = db.execute('INSERT INTO report (plan_id, created_by, snapshot, fingerprint) VALUES (%s,%s,%s,%s) '
                            'RETURNING id, state, fingerprint', (plan_id, actor, Jsonb(snapshot), digest)).fetchone()
        record(db, actor, 'run_queued', str(report['id']), {'fingerprint': digest})
    try:
        queue.lpush(WAKE_KEY, 'pending')
    except RedisError:
        LOGGER.warning('Redis wake-up failed, worker will poll PostgreSQL')
    return report


def list_reports(user):
    with connect() as db:
        return db.execute('''
            SELECT r.id, r.state, r.created_by AS actor, r.created_at, r.decision, p.edition, p.route_code
            FROM report AS r JOIN analysis_plan AS p ON p.id=r.plan_id
            WHERE (%s OR r.state='published') ORDER BY r.id DESC
        ''', (user['role'] != Role.VIEWER,)).fetchall()


def report_or_error(db, report_id, user, lock=False):
    suffix = ' FOR UPDATE' if lock else ''
    report = db.execute('SELECT * FROM report WHERE id=%s' + suffix, (report_id,)).fetchone()
    if report is None or (user['role'] == Role.VIEWER and report['state'] != RunState.PUBLISHED):
        raise HTTPException(404, '未找到可阅报告')
    return report


def get_report(report_id, user):
    with connect() as db:
        return report_or_error(db, report_id, user)


def publish(report_id, review, user):
    with connect() as db:
        report = report_or_error(db, report_id, user, lock=True)
        if report['state'] != RunState.READY:
            raise HTTPException(409, '仅可发布已完成且待复核的报告')
        if review.decision not in report['result']['decisions']:
            raise HTTPException(422, '当前数据和告警状态不支持此决定')
        report = db.execute('''
            UPDATE report SET state='published', decision=%s, review_note=%s, reviewed_by=%s, reviewed_at=now()
            WHERE id=%s RETURNING *
        ''', (review.decision, review.note, user['username'], report_id)).fetchone()
        record(db, user['username'], 'report_published', str(report_id), review.model_dump(mode='json'))
        return report
