from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


app = FastAPI(name='AnarchoLib')


# app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates('templates')

@app.get('/')
async def root(request: Request):
    return templates.TemplateResponse(name='index.html', request=request)


@app.get('/literature')
async def literature(request: Request):
    return templates.TemplateResponse(name='literature.html', request=request)
