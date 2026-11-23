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
        os.replace(temp, export_path(report_id))
    finally:
        if temp and os.path.exists(temp):
            os.unlink(temp)
