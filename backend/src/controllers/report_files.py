from fastapi import HTTPException
from fastapi.responses import FileResponse

from src.constants.domain import RunState
from src.services.export import export_path
from src.services.reports import get_report


def download(report_id, user):
    report = get_report(report_id, user)
    if report['state'] not in (RunState.READY, RunState.PUBLISHED):
        raise HTTPException(409, '报告尚未生成导出文件')
    path = export_path(report_id)
    if not path.is_file():
        raise HTTPException(503, '导出文件暂不可用，请重新运行分析')
    return FileResponse(path, filename=path.name, media_type='text/csv; charset=utf-8')
