import csv
import os
from tempfile import NamedTemporaryFile

from src.config.settings import EXPORT_DIR


METRICS = ('complete', 'blocked', 'raw_change', 'treatment', 'period', 'sequence_gap', 'first_period', 'imbalance', 'sequence_alert')


def export_path(report_id):
    return EXPORT_DIR / f'ramp-report-{report_id}.csv'


def write_export(report_id, snapshot, fingerprint, result):
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    temp = None
    try:
        # Same mount as the destination so replacement is atomic across workers.
        with NamedTemporaryFile(dir=EXPORT_DIR, mode='w', encoding='utf-8-sig', newline='', delete=False) as output:
            temp = output.name
            writer = csv.writer(output)
            writer.writerow(['method', 'snapshot_sha256', 'plan_id', 'min_pairs', 'gap_limit_seconds'])
            plan = snapshot['plan']
            writer.writerow([snapshot['method'], fingerprint, plan['id'], plan['min_pairs'], plan['gap_limit']])
            writer.writerow(METRICS)
            writer.writerow([result[key] for key in METRICS])
            writer.writerow(['sequence', 'enrolled', 'complete', 'period1_seconds', 'period2_seconds', 'change_seconds'])
            for sequence, group in result['groups'].items():
                writer.writerow([sequence, *(group[key] for key in ('enrolled', 'complete', 'period1', 'period2', 'change'))])
            writer.writerow(['participant', 'sequence', 'period1_seconds', 'period2_seconds', 'complete'])
            for row in snapshot['pairs']:
                writer.writerow([row['code'], row['sequence'], row['period1'], row['period2'], row['period1'] is not None and row['period2'] is not None])
            randomized = result.get('randomized') or {}
            writer.writerow(['randomized_test', 'status', 'started_groups', 'complete_groups', 'benefit_seconds', 'p_value', 'p_numerator', 'p_denominator', 'p_method'])
            writer.writerow(['randomization.paired-order.v1', randomized.get('status'), randomized.get('started_groups'),
                             randomized.get('complete_groups'), randomized.get('benefit'), randomized.get('p_value'),
                             randomized.get('p_numerator'), randomized.get('p_denominator'), randomized.get('p_method')])
            writer.writerow(['slot', 'seat', 'participant', 'sequence', 'started_at', 'period1_seconds', 'period2_seconds', 'delta_ab_seconds', 'delta_ba_seconds'])
            for group in randomized.get('groups', []):
                for member in group['members']:
                    writer.writerow([group['slot_code'], member['seat'], member['participant_code'], member['sequence'],
                                     group['started_at'], member['period1'], member['period2'],
                                     group['delta_ab'], group['delta_ba']])
            writer.writerow(['slot', 'seat', 'participant', 'sequence', 'missing_periods'])
            for item in randomized.get('missing', []):
                writer.writerow([item['slot_code'], item.get('seat') or '', item['participant_code'] or '', item['sequence'] or '', '、'.join(item['periods'])])
        os.replace(temp, export_path(report_id))
    finally:
        if temp and os.path.exists(temp):
            os.unlink(temp)
