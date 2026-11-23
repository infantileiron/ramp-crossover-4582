import secrets
from decimal import Decimal

from fastapi import HTTPException

from src.config.database import connect
from src.services.audit import record
from src.services.field import route_or_error

SEQUENCES = ('AB', 'BA')


def opposite(sequence):
    return 'BA' if sequence == 'AB' else 'AB'


def _member_rows(db, session_id):
    return db.execute(
        'SELECT seat, participant_code, period1, period2 FROM session_member '
        'WHERE session_id=%s ORDER BY seat', (session_id,),
    ).fetchall()


def _assignment_rows(db, session_id):
    return db.execute(
        'SELECT seat, participant_code, sequence FROM session_assignment '
        'WHERE session_id=%s ORDER BY seat', (session_id,),
    ).fetchall()


def _view(db, row, with_assignment=True):
    session = {
        'id': row['id'],
        'route_code': row['route_code'],
        'slot_code': row['slot_code'],
        'starts_at': row['starts_at'],
        'started_at': row['started_at'],
        'started_seat': row['started_seat'],
        'started_code': row['started_code'],
        'locked': row['started_at'] is not None,
        'members': _member_rows(db, row['id']),
        'assignment': _assignment_rows(db, row['id']) if with_assignment and row['started_at'] else [],
    }
    return session


def sessions(route_code):
    with connect() as db:
        route_or_error(db, route_code)
        rows = db.execute(
            'SELECT * FROM field_session WHERE route_code=%s ORDER BY starts_at, id', (route_code,),
        ).fetchall()
        return [_view(db, row) for row in rows]


def _session_or_error(db, session_id, lock=False):
    suffix = ' FOR UPDATE' if lock else ''
    row = db.execute('SELECT * FROM field_session WHERE id=%s' + suffix, (session_id,)).fetchone()
    if row is None:
        raise HTTPException(404, '未找到该时段分组')
    return row


def create_session(route_code, data, actor):
    if data.seat1_code == data.seat2_code:
        raise HTTPException(422, '同一分组的两位参与者编号不能相同')
    sealed = secrets.choice(SEQUENCES)
    with connect() as db:
        route_or_error(db, route_code)
        session = db.execute('''
            INSERT INTO field_session (route_code, slot_code, starts_at, sealed_seat1_sequence, created_by)
            VALUES (%s,%s,%s,%s,%s)
            ON CONFLICT (route_code, slot_code) DO NOTHING
            RETURNING *
        ''', (route_code, data.slot_code, data.starts_at, sealed, actor)).fetchone()
        if session is None:
            raise HTTPException(409, '此路线已有同名时段')
        for seat, code in ((1, data.seat1_code), (2, data.seat2_code)):
            try:
                db.execute('INSERT INTO session_member (session_id, route_code, seat, participant_code) '
                           'VALUES (%s,%s,%s,%s)', (session['id'], route_code, seat, code))
            except Exception as exc:
                if getattr(exc, 'sqlstate', None) == '23505':
                    raise HTTPException(409, f'参与者 {code} 已在该路线的其他分组中') from exc
                raise
        record(db, actor, 'session_created', f'{route_code}/{data.slot_code}', {'seat1': data.seat1_code, 'seat2': data.seat2_code})
        return _view(db, session)


def swap_member(session_id, seat, data, actor):
    """Replace a participant before departure.

    The session row is locked first, so a concurrent reveal either commits
    before this swap (and the swap is refused because the group is locked) or
    waits until the swap commits.  The previous member's recorded times are
    cleared so they can never be attributed to the replacement.
    """
    with connect() as db:
        session = _session_or_error(db, session_id, lock=True)
        if session['started_at'] is not None:
            raise HTTPException(409, '分组已开走并锁定，不能再更换成员')
        if seat not in (1, 2):
            raise HTTPException(422, '席位无效')
        current = db.execute('SELECT participant_code FROM session_member WHERE session_id=%s AND seat=%s',
                             (session_id, seat)).fetchone()
        if current is None:
            raise HTTPException(404, '未找到该席位的成员')
        if current['participant_code'] == data.participant_code:
            return _view(db, session)
        other = db.execute('SELECT participant_code FROM session_member WHERE session_id=%s AND seat<>%s',
                           (session_id, seat)).fetchone()
        if other is not None and other['participant_code'] == data.participant_code:
            raise HTTPException(409, '该参与者已在此分组的另一席位')
        try:
            db.execute('UPDATE session_member SET participant_code=%s, period1=NULL, period2=NULL, updated_at=now() '
                       'WHERE session_id=%s AND seat=%s', (data.participant_code, session_id, seat))
        except Exception as exc:
            if getattr(exc, 'sqlstate', None) == '23505':
                raise HTTPException(409, f'参与者 {data.participant_code} 已在该路线的其他分组中') from exc
            raise
        record(db, actor, 'session_member_swapped', f'{session["route_code"]}/{session["slot_code"]}',
               {'seat': seat, 'from': current['participant_code'], 'to': data.participant_code})
        return _view(db, session)


def start_session(session_id, data, actor):
    """Reveal the sealed order for the participant who sets off and lock the group.

    Idempotent: once ``started_at`` is committed, repeating the call returns
    the same confirmed assignment.  If the first attempt fails before commit,
    the sealed order is still fixed on the session row, so a retry reveals the
    same order rather than drawing a new one.
    """
    with connect() as db:
        session = _session_or_error(db, session_id, lock=True)
        if session['started_at'] is not None:
            return _view(db, session)
        if data.seat not in (1, 2):
            raise HTTPException(422, '席位无效')
        members = {row['seat']: row for row in _member_rows(db, session_id)}
        if len(members) != 2:
            raise HTTPException(409, '分组尚未凑齐两人，无法开走')
        member = members.get(data.seat)
        if member is None:
            raise HTTPException(404, '未找到该席位的成员')
        if member['participant_code'] != data.participant_code:
            # A concurrent swap replaced the departing member after the client
            # read the group.  Never bind the old member's order to the new one.
            raise HTTPException(409, '该席位成员已被更换，请确认实际开走的人员后再试')
        seat1_sequence = session['sealed_seat1_sequence']
        for seat in (1, 2):
            sequence = seat1_sequence if seat == 1 else opposite(seat1_sequence)
            db.execute('INSERT INTO session_assignment (session_id, seat, participant_code, sequence) '
                       'VALUES (%s,%s,%s,%s) ON CONFLICT (session_id, seat) DO NOTHING',
                       (session_id, seat, members[seat]['participant_code'], sequence))
        db.execute('UPDATE field_session SET started_at=now(), started_seat=%s, started_code=%s WHERE id=%s',
                   (data.seat, data.participant_code, session_id))
        record(db, actor, 'session_started', f'{session["route_code"]}/{session["slot_code"]}',
               {'seat': data.seat, 'participant_code': data.participant_code, 'seat1_sequence': seat1_sequence})
        return _view(db, _session_or_error(db, session_id))


def record_times(session_id, seat, data, actor):
    with connect() as db:
        session = _session_or_error(db, session_id, lock=True)
        if seat not in (1, 2):
            raise HTTPException(422, '席位无效')
        if session['started_at'] is None:
            raise HTTPException(409, '分组尚未开走，顺序未揭晓，暂不能录入用时')
        member = db.execute('SELECT participant_code FROM session_member WHERE session_id=%s AND seat=%s',
                            (session_id, seat)).fetchone()
        if member is None:
            raise HTTPException(404, '未找到该席位的成员')
        assignment = db.execute('SELECT participant_code FROM session_assignment WHERE session_id=%s AND seat=%s',
                               (session_id, seat)).fetchone()
        if assignment is None or assignment['participant_code'] != member['participant_code']:
            raise HTTPException(409, '该席位成员与开走时确认的分派不一致，不能记录用时')
        db.execute('UPDATE session_member SET period1=%s, period2=%s, updated_at=now() '
                   'WHERE session_id=%s AND seat=%s',
                   (data.period1, data.period2, session_id, seat))
        record(db, actor, 'session_times_saved', f'{session["route_code"]}/{session["slot_code"]}',
               {'seat': seat, 'period1': str(data.period1), 'period2': str(data.period2)})
        return _view(db, _session_or_error(db, session_id))


def _iso(value):
    return value.isoformat() if hasattr(value, 'isoformat') else value


def snapshot_sessions(db, route_code):
    """Started groups only: an unreleased sealed order must not enter a snapshot."""
    rows = db.execute('SELECT * FROM field_session WHERE route_code=%s AND started_at IS NOT NULL '
                      'ORDER BY starts_at, id', (route_code,)).fetchall()
    snapshot = []
    for row in rows:
        members = db.execute(
            'SELECT m.seat, m.participant_code, m.period1, m.period2, a.sequence '
            'FROM session_member AS m JOIN session_assignment AS a '
            'ON a.session_id=m.session_id AND a.seat=m.seat '
            'WHERE m.session_id=%s ORDER BY m.seat', (row['id'],),
        ).fetchall()
        snapshot.append({
            'slot_code': row['slot_code'],
            'starts_at': _iso(row['starts_at']),
            'started_at': _iso(row['started_at']),
            'started_seat': row['started_seat'],
            'started_code': row['started_code'],
            'members': [{
                'seat': member['seat'],
                'participant_code': member['participant_code'],
                'sequence': member['sequence'],
                'period1': format(member['period1'], '.2f') if isinstance(member['period1'], Decimal) else member['period1'],
                'period2': format(member['period2'], '.2f') if isinstance(member['period2'], Decimal) else member['period2'],
            } for member in members],
        })
    return snapshot
