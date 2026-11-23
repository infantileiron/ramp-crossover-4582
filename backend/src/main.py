from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from psycopg import Error as DatabaseError
from redis.exceptions import RedisError

from src.config.database import connect, queue
from src.middlewares.http import error_boundary, request_context
from src.routes import auth, field, reports

app = FastAPI(title='岔路导览', version='1.0.0')
app.middleware('http')(error_boundary)
app.middleware('http')(request_context)
for module in (auth, field, reports):
    app.include_router(module.router)


@app.exception_handler(RequestValidationError)
async def invalid_input(_, error):
    fields = [{'field': '.'.join(map(str, item['loc'][1:])), 'reason': item['msg']} for item in error.errors()]
    return JSONResponse(status_code=422, content={'detail': '请检查录入范围及必填项。', 'fields': fields})


@app.get('/health')
def health():
    try:
        with connect() as db:
            db.execute('SELECT 1 FROM field_route LIMIT 1')
        queue.ping()
    except (DatabaseError, RedisError) as exc:
        raise HTTPException(503, '依赖服务暂不可用') from exc
    return {'status': 'ok', 'database': 'ok', 'redis': 'ok'}
