from decimal import Decimal
from statistics import mean

from src.constants.domain import Decision, Sequence
from src.services.randomized import analyze_randomized

METHOD = 'crossover.two-period.v1'


def summarize(rows):
    paired = [row for row in rows if row['period1'] is not None and row['period2'] is not None]
    incomplete = [row['code'] for row in rows if row['period1'] is None or row['period2'] is None]
    summary = {'enrolled': len(rows), 'complete': len(paired), 'incomplete': incomplete,
               'period1': None, 'period2': None, 'change': None, 'level': None}
    if paired:
        first = mean(Decimal(row['period1']) for row in paired)
        second = mean(Decimal(row['period2']) for row in paired)
        summary.update(period1=first, period2=second, change=second-first, level=(first+second)/2)
    return summary


def analyze(snapshot):
    settings = snapshot['plan']
    groups = {sequence: summarize([row for row in snapshot['pairs'] if row['sequence'] == sequence]) for sequence in Sequence}
    ab, ba = groups[Sequence.AB], groups[Sequence.BA]
    count = ab['complete'] + ba['complete']
    complete_groups = [group for group in groups.values() if group['complete']]
    trend = (sum(group['complete'] * group['change'] for group in complete_groups) / count) if count else None
    has_both_groups = len(complete_groups) == 2
    blocked = any(group['complete'] < settings['min_pairs'] for group in groups.values())
    gap = ba['level'] - ab['level'] if has_both_groups else None
    first_period = ba['period1'] - ab['period1'] if has_both_groups else None
    imbalanced = ab['complete'] != ba['complete']
    gap_alert = gap is not None and abs(gap) >= Decimal(settings['gap_limit'])
    treatment = (ab['change'] - ba['change']) / 2 if not blocked else None
    period = (ab['change'] + ba['change']) / 2 if not blocked else None
    alerts = []
    if blocked:
        alerts.append('至少一个顺序未达到完整配对门槛，处理差和时期差暂不估计。')
    if ab['incomplete'] or ba['incomplete']:
        alerts.append('未完成两轮的参与者已从全部用时比较中剔除，缺测可能影响代表性。')
    if imbalanced:
        alerts.append('两序列完整人数不同。总体变化按人数计，处理差与时期差按序列等权计。')
    if gap_alert:
        alerts.append('两序列的双轮平均用时差达到复核线。应复核基线差异、环境变化及上一轮指引的延续影响。')
    decisions = [Decision.RETEST, Decision.RETAIN]
    if not blocked and not gap_alert and not imbalanced and treatment < 0:
        decisions.append(Decision.PILOT)
    randomized = analyze_randomized(snapshot.get('sessions') or [])
    return {
        'method': METHOD, 'groups': groups, 'complete': count, 'blocked': blocked,
        'raw_change': trend, 'treatment': treatment, 'period': period, 'sequence_gap': gap,
        'first_period': first_period, 'imbalance': imbalanced, 'sequence_alert': gap_alert,
        'randomized': randomized,
        'alerts': alerts, 'decisions': decisions,
    }
