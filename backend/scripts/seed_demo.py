import json

from src.config.database import connect
from src.utils.passwords import hash_password

ACCOUNTS = (
    ('reviewer', '程岚', 'reviewer', 'Review5215!'),
    ('analyst', '沈栩', 'analyst', 'Analyze5215!'),
    ('viewer', '陶桥', 'viewer', 'View5215!'),
)
ROUTE = (
    'R07', '北门连廊坡道', '北门入口', '连廊平台', 86,
    '由入口经过花坛岔口至连廊平台。两轮走同一条路线，期间更换岔口的指引。',
    '文字箭头牌', '坡道图标牌',
)
PAIRS = (
    ('AB01', 'AB', 60, 42), ('AB02', 'AB', 64, 52), ('AB03', 'AB', 75, 51),
    ('AB04', 'AB', 70, 50), ('AB05', 'AB', 65, 49), ('AB06', 'AB', 68, 50),
    ('AB07', 'AB', 72, None),
    ('BA01', 'BA', 65, 69), ('BA02', 'BA', 76, 76), ('BA03', 'BA', 70, 74),
    ('BA04', 'BA', 73, 73), ('BA05', 'BA', None, 79),
)
# Started two-person groups with the revealed order already recorded.  Times are
# chosen so the sealed orders below describe the demo without any hidden state.
# The last slot is still pending: its order stays sealed and it can still swap
# members until someone sets off.
SESSIONS = (
    ('T0900', '2026-11-23 09:00+08', 'P0901', 1, 'P0902', 'AB', (63, 47), (69, 71)),
    ('T0920', '2026-11-23 09:20+08', 'P0921', 2, 'P0922', 'BA', (66, 70), (58, 49)),
    ('T0940', '2026-11-23 09:40+08', 'P0941', 1, 'P0942', 'AB', (74, 52), (72, 73)),
    ('T1000', '2026-11-23 10:00+08', 'P1001', 2, 'P1002', 'BA', (71, 68), (67, 53)),
)
PENDING_SESSIONS = (
    ('T1020', '2026-11-23 10:20+08', 'P1021', 'P1022'),
)


def seed_sessions(db):
    for slot, starts_at, seat1_code, started_seat, seat2_code, seat1_sequence, seat1_times, seat2_times in SESSIONS:
        session = db.execute(
            'INSERT INTO field_session (route_code, slot_code, starts_at, sealed_seat1_sequence, '
            'started_at, started_seat, started_code, created_by) '
            "VALUES (%s,%s,%s,%s,%s,%s,%s,'analyst') ON CONFLICT (route_code, slot_code) DO NOTHING RETURNING id",
            (ROUTE[0], slot, starts_at, seat1_sequence, starts_at, started_seat,
             seat1_code if started_seat == 1 else seat2_code),
        ).fetchone()
        if session is None:
            continue
        for seat, code, periods in ((1, seat1_code, seat1_times), (2, seat2_code, seat2_times)):
            db.execute('INSERT INTO session_member (session_id, route_code, seat, participant_code, period1, period2) '
                       'VALUES (%s,%s,%s,%s,%s,%s)', (session['id'], ROUTE[0], seat, code, *periods))
            sequence = seat1_sequence if seat == 1 else ('BA' if seat1_sequence == 'AB' else 'AB')
            db.execute('INSERT INTO session_assignment (session_id, seat, participant_code, sequence) '
                       'VALUES (%s,%s,%s,%s)', (session['id'], seat, code, sequence))
    for slot, starts_at, seat1_code, seat2_code in PENDING_SESSIONS:
        session = db.execute(
            'INSERT INTO field_session (route_code, slot_code, starts_at, sealed_seat1_sequence, created_by) '
            "VALUES (%s,%s,%s,%s,'analyst') ON CONFLICT (route_code, slot_code) DO NOTHING RETURNING id",
            (ROUTE[0], slot, starts_at, 'AB'),
        ).fetchone()
        if session is None:
            continue
        for seat, code in ((1, seat1_code), (2, seat2_code)):
            db.execute('INSERT INTO session_member (session_id, route_code, seat, participant_code) '
                       'VALUES (%s,%s,%s,%s)', (session['id'], ROUTE[0], seat, code))


def seed():
    with connect() as db, db.cursor() as cursor:
        cursor.executemany(
            'INSERT INTO app_user (username, display_name, role, password_hash) VALUES (%s,%s,%s,%s) '
            'ON CONFLICT (username) DO NOTHING',
            [(username, name, role, hash_password(password)) for username, name, role, password in ACCOUNTS],
        )
        cursor.execute('INSERT INTO field_route VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING', ROUTE)
        cursor.executemany(
            'INSERT INTO field_pair (route_code, code, sequence, period1, period2) VALUES (%s,%s,%s,%s,%s) '
            'ON CONFLICT (route_code, code) DO NOTHING',
            [(ROUTE[0], *row) for row in PAIRS],
        )
        cursor.execute(
            'INSERT INTO analysis_plan (route_code, edition, min_pairs, gap_limit, created_by) '
            "VALUES (%s,'现场初核',3,8,'analyst') ON CONFLICT (route_code, edition) DO NOTHING", (ROUTE[0],),
        )
        seed_sessions(db)
        keys = {
            'users': [row['username'] for row in db.execute('SELECT username FROM app_user ORDER BY username')],
            'routes': [row['code'] for row in db.execute('SELECT code FROM field_route ORDER BY code')],
            'pairs': [list(row.values()) for row in db.execute('SELECT route_code, code FROM field_pair ORDER BY route_code, code')],
            'plans': [list(row.values()) for row in db.execute('SELECT route_code, edition FROM analysis_plan ORDER BY route_code, edition')],
            'sessions': [list(row.values()) for row in db.execute('SELECT route_code, slot_code FROM field_session ORDER BY route_code, slot_code')],
        }
    print(json.dumps(keys, ensure_ascii=False, sort_keys=True))


if __name__ == '__main__':
    seed()
