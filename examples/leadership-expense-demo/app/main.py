from app.security import RequestSizeLimit
from pathlib import Path
import json
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from app.core import reconcile

ROOT = Path(__file__).resolve().parent.parent
app = FastAPI(title='Education Fund · Expense reconciliation demo', version='0.1.0', description='Synthetic local demonstration. Arithmetic only. No payments, email delivery, or accounting writes. Do not expose publicly without authentication.')
app.add_middleware(TrustedHostMiddleware, allowed_hosts=['127.0.0.1','localhost','testserver'])
app.add_middleware(RequestSizeLimit)
app.mount('/static', StaticFiles(directory=ROOT/'app/static'), name='static')

@app.middleware('http')
async def headers(request, call_next):
    if request.url.path.startswith('/api/'):
        origin = request.headers.get('origin')
        if (origin and origin != str(request.base_url).rstrip('/')) or request.headers.get('sec-fetch-site') == 'cross-site':
            return JSONResponse({'detail': 'Foreign origin rejected'}, status_code=403)
    response = await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Referrer-Policy']='no-referrer'
    response.headers['Cache-Control']='no-store'
    if request.url.path == '/':
        response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
    return response

@app.get('/', include_in_schema=False)
def index(): return FileResponse(ROOT/'app/static/index.html')

@app.get('/api/example')
def example(): return json.loads((ROOT/'examples/balanced.json').read_text())

@app.post('/api/reconcile', operation_id='reconcileExpenseReport', openapi_extra={'requestBody': {'required': True, 'content': {'application/json': {'schema': {'type': 'object'}, 'example': json.loads((ROOT/'examples/balanced.json').read_text())}}}})
async def calculate(request: Request):
    # Bound actual bytes, not just a caller-supplied Content-Length.
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body)>131072: raise HTTPException(413,'Maximum request size is 128 KiB.')
    try:
        data=json.loads(body)
        if not isinstance(data,dict): raise ValueError('Expected a JSON object.')
        return reconcile(data)
    except (ValueError, TypeError, KeyError, RecursionError) as exc:
        raise HTTPException(422,str(exc)) from exc
