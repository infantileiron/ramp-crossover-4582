"""Randomisation test for paired walking-order groups.

Each started time slot contains two participants; the sealed random order is
revealed when either participant sets off.  For the report we ask how often a
fresh random assignment of AB/BA inside the original groups would produce an
icon (B) benefit at least as large as the one observed.  Reversing a group's
order flips the sign of its treatment contribution, so the exact distribution
is the distribution of ``sum(sign_g * contribution_g)`` with ``sign_g`` equally
likely to be +1 or -1.
"""

from collections import Counter
from decimal import Decimal
from math import gcd
from random import Random

from src.constants.domain import Sequence

# A group's contribution is half the difference of its two deltas.  With two
# decimal places on every input, that contribution is a multiple of 0.005 s, so
# 200 units per second keeps the exact enumeration integral.
UNITS_PER_SECOND = 200
MONTE_CARLO_DRAWS = 100_000
MONTE_CARLO_SEED = 5215

SEQUENCES = (Sequence.AB, Sequence.BA)


def _present(value):
    return value is not None and value != ''


def _seconds(value):
    return Decimal(str(value))


def _exact_tail(units):
    """Count sign assignments whose pooled benefit reaches the observed one.

    Each ``unit`` is a group's contribution expressed in 0.005 s.  Observed
    benefit is ``-sum(u) / (2 * n)`` units; a flipped assignment gives
    ``-sum(s_g * u_g) / (2 * n)``.  So ``benefit_flipped >= benefit_observed``
    is equivalent to ``sum(s_g * u_g) <= sum(u_g)``, independent of the scale.
    """
    divisor = 0
    for unit in units:
        divisor = gcd(divisor, abs(unit))
    scaled = [unit // divisor for unit in units] if divisor else [0 for _ in units]
    distribution = Counter({0: 1})
    for unit in scaled:
        following = Counter()
        for total, count in distribution.items():
            following[total + unit] += count
            following[total - unit] += count
        if len(following) > 2_000_000:
            return None
        distribution = following
    observed = sum(scaled)
    return sum(count for total, count in distribution.items() if total <= observed), 2 ** len(units)


def _monte_carlo_tail(units):
    generator = Random(MONTE_CARLO_SEED + len(units))
    observed = sum(units)
    reached = 0
    for _ in range(MONTE_CARLO_DRAWS):
        total = 0
        for unit in units:
            total += unit if generator.random() < 0.5 else -unit
        if total <= observed:
            reached += 1
    return reached, MONTE_CARLO_DRAWS


def _missing_item(session, member, periods):
    return {
        'slot_code': session.get('slot_code'),
        'seat': member.get('seat') if member else None,
        'participant_code': member.get('participant_code') if member else None,
        'sequence': member.get('sequence') if member else None,
        'periods': periods,
    }


def analyze_randomized(sessions):
    """Evaluate started two-person groups as a randomisation test.

    Only groups that have set off are eligible.  Any missing round in a
    started group suspends the test instead of silently dropping the group.
    """
    started = [session for session in sessions if session.get('started_at')]
    groups = []
    units = []
    missing = []

    for session in started:
        members = session.get('members') or []
        by_sequence = {}
        for member in members:
            sequence = member.get('sequence')
            if sequence in SEQUENCES:
                by_sequence[sequence] = member

        absent = []
        if len(members) != 2 or any(sequence not in by_sequence for sequence in SEQUENCES):
            absent.append('成员或已确认的分派顺序')
        if absent:
            missing.append(_missing_item(session, None, absent))
            continue

        session_missing = []
        for sequence in SEQUENCES:
            member = by_sequence[sequence]
            periods = []
            if not _present(member.get('period1')):
                periods.append('第1轮')
            if not _present(member.get('period2')):
                periods.append('第2轮')
            if periods:
                session_missing.append(_missing_item(session, member, periods))
        if session_missing:
            missing.extend(session_missing)
            continue

        first = by_sequence[Sequence.AB]
        second = by_sequence[Sequence.BA]
        delta_ab = _seconds(first['period2']) - _seconds(first['period1'])
        delta_ba = _seconds(second['period2']) - _seconds(second['period1'])
        difference = delta_ab - delta_ba
        groups.append({
            'slot_code': session.get('slot_code'),
            'starts_at': session.get('starts_at'),
            'started_at': session.get('started_at'),
            'started_seat': session.get('started_seat'),
            'members': [
                {
                    'seat': first.get('seat'),
                    'participant_code': first.get('participant_code'),
                    'sequence': Sequence.AB.value,
                    'period1': first.get('period1'),
                    'period2': first.get('period2'),
                },
                {
                    'seat': second.get('seat'),
                    'participant_code': second.get('participant_code'),
                    'sequence': Sequence.BA.value,
                    'period1': second.get('period1'),
                    'period2': second.get('period2'),
                },
            ],
            'delta_ab': delta_ab,
            'delta_ba': delta_ba,
            'contribution': difference / 2,
        })
        units.append(int(difference * UNITS_PER_SECOND))

    result = {
        'status': 'empty',
        'test': 'randomization.paired-order.v1',
        'started_groups': len(started),
        'complete_groups': len(groups),
        'groups': [],
        'missing': missing,
        'benefit': None,
        'p_value': None,
        'p_numerator': None,
        'p_denominator': None,
        'p_method': None,
        'reason': None,
    }

    if missing:
        result.update(status='blocked', groups=groups)
        labels = []
        for item in missing:
            who = item['participant_code'] or item['slot_code']
            labels.append(f"{item['slot_code']} / {who}（{'、'.join(item['periods'])}）")
        result['reason'] = '已开走的分组存在缺测或分派缺失，暂缓随机分派检验：' + '；'.join(labels) + '。'
        return result

    if not groups:
        result['reason'] = '尚无两轮齐全且已开走的随机分组。'
        return result

    total_units = sum(units)
    count = len(groups)
    # A unit is 0.005 s of each group's contribution, and the pooled benefit is
    # the mean of the per-group contributions: total_units / 2 / (200 * count).
    benefit = Decimal(-total_units) / Decimal(2 * UNITS_PER_SECOND * count)
    exact = _exact_tail(units)
    if exact is not None:
        numerator, denominator = exact
        method = 'exact'
    else:
        # Enumeration hit its budget (many wide contributions); fall back to a
        # fixed-seed sample and disclose the draw count as the denominator.
        numerator, denominator = _monte_carlo_tail(units)
        method = 'monte-carlo'
    result.update(
        status='ready',
        groups=groups,
        benefit=benefit,
        p_value=numerator / denominator,
        p_numerator=numerator,
        p_denominator=denominator,
        p_method=method,
        reason='在每个原分组内互换两名成员的 AB/BA 顺序，统计随机分派下图标收益不低于实测值的机会。',
    )
    return result
