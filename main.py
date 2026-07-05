from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from actions import app as actions_app


app = FastAPI(name='AnarchoLib')
app.include_router(router=actions_app)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates('templates')

@app.get('/')
async def root(request: Request):
    return templates.TemplateResponse(name='index.html', request=request)


@app.get('/literature')
async def literature(request: Request):
    return templates.TemplateResponse(name='literature.html', request=request)


@app.get('/faq')
async def faq(request: Request):
    return templates.TemplateResponse(name='faq.html', request=request)


@app.get('/contacts')
async def contacts(request: Request):
    return templates.TemplateResponse(name='contacts.html', request=request)
