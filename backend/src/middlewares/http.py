import logging
from uuid import uuid4

from fastapi.responses import JSONResponse

LOGGER = logging.getLogger(__name__)


async def request_context(request, call_next):
    request_id = uuid4().hex
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers['X-Request-ID'] = request_id
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


async def error_boundary(request, call_next):
    try:
        return await call_next(request)
    except Exception:
        LOGGER.exception('Request %s failed', request.state.request_id)
        return JSONResponse(status_code=500, content={'detail': '操作未能完成，请重试。', 'request_id': request.state.request_id})
