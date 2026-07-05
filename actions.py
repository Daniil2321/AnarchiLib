from fastapi import FastAPI, HTTPException, Depends, APIRouter, File, UploadFile
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.requests import Request
from typing import List, Optional
import datetime
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from db.database import (
    engine, SessionLocal, Action as DBAction, ActionImage as DBImage,
    create_tables
)
import os
import shutil
import uuid
from fastapi.templating import Jinja2Templates


UPLOAD_DIR = "static/uploads"

app = APIRouter()

# Монтирование статики (если ещё не сделано)
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory='templates')

@app.on_event("startup")
def startup():
    create_tables()

# ---------- Модели для акций ----------
# ----- Зависимость для получения сессии БД -----
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ----- Pydantic-модели -----
class ActionBase(BaseModel):
    title: str
    description: Optional[str] = None
    date: str
    location: str
    status: str = "planned"

class ActionCreate(ActionBase):
    pass

class ActionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    date: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None

class ActionResponse(ActionBase):
    id: int
    created_at: datetime.datetime
    images: List[str] = []   # список URL изображений

    class Config:
        from_attributes = True

class ImageResponse(BaseModel):
    id: int
    url: str


# ----- Эндпоинты -----
@app.get('/actions')
async def actions(request: Request):
    return templates.TemplateResponse(name='actions.html', request=request)

@app.get('/actions/rules')
async def actions(request: Request):
    return templates.TemplateResponse(name='actions_rules.html', request=request)

@app.get('/actions/examples')
async def actions(request: Request):
    return templates.TemplateResponse(name='actions_examples.html', request=request)

@app.get("/api/actions", response_model=List[ActionResponse])
def get_actions(db: Session = Depends(get_db)):
    """Получить все акции (с изображениями)"""
    actions = db.query(DBAction).order_by(DBAction.created_at.desc()).all()
    result = []
    for action in actions:
        img_urls = [img.url for img in action.images]
        result.append(ActionResponse(
            id=action.id,
            title=action.title,
            description=action.description,
            date=action.date,
            location=action.location,
            status=action.status,
            created_at=action.created_at,
            images=img_urls
        ))
    return result


@app.get("/api/actions/{action_id}", response_model=ActionResponse)
def get_action(action_id: int, db: Session = Depends(get_db)):
    action = db.query(DBAction).filter(DBAction.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Акция не найдена")
    img_urls = [img.url for img in action.images]
    return ActionResponse(
        id=action.id,
        title=action.title,
        description=action.description,
        date=action.date,
        location=action.location,
        status=action.status,
        created_at=action.created_at,
        images=img_urls
    )


@app.post("/api/actions", response_model=ActionResponse)
def create_action(action: ActionCreate, db: Session = Depends(get_db)):
    new_action = DBAction(
        title=action.title,
        description=action.description,
        date=action.date,
        location=action.location,
        status=action.status,
        created_at=datetime.datetime.now()
    )
    db.add(new_action)
    db.commit()
    db.refresh(new_action)
    return ActionResponse(
        id=new_action.id,
        title=new_action.title,
        description=new_action.description,
        date=new_action.date,
        location=new_action.location,
        status=new_action.status,
        created_at=new_action.created_at,
        images=[]
    )


@app.put("/api/actions/{action_id}", response_model=ActionResponse)
def update_action(action_id: int, action_update: ActionUpdate, db: Session = Depends(get_db)):
    action = db.query(DBAction).filter(DBAction.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Акция не найдена")

    # Обновляем только переданные поля
    update_data = action_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(action, key, value)

    db.commit()
    db.refresh(action)

    img_urls = [img.url for img in action.images]
    return ActionResponse(
        id=action.id,
        title=action.title,
        description=action.description,
        date=action.date,
        location=action.location,
        status=action.status,
        created_at=action.created_at,
        images=img_urls
    )


@app.delete("/api/actions/{action_id}")
def delete_action(action_id: int, db: Session = Depends(get_db)):
    action = db.query(DBAction).filter(DBAction.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Акция не найдена")
    # Удаляем связанные изображения с диска
    for img in action.images:
        file_path = os.path.join(".", img.url.lstrip("/"))
        if os.path.exists(file_path):
            os.remove(file_path)
    db.delete(action)
    db.commit()
    return {"ok": True}


# ----- Работа с изображениями -----
@app.post("/api/actions/{action_id}/images", response_model=ImageResponse)
async def upload_image(action_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    action = db.query(DBAction).filter(DBAction.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Акция не найдена")

    # Генерируем уникальное имя файла
    ext = os.path.splitext(file.filename)[1]
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    # Сохраняем файл
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    url = f"/static/uploads/{unique_name}"

    new_image = DBImage(
        filename=file.filename,
        url=url,
        action_id=action_id
    )
    db.add(new_image)
    db.commit()
    db.refresh(new_image)

    return ImageResponse(id=new_image.id, url=url)


@app.delete("/api/actions/images/{image_id}")
def delete_image(image_id: int, db: Session = Depends(get_db)):
    image = db.query(DBImage).filter(DBImage.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Изображение не найдено")

    # Удаляем файл с диска
    file_path = os.path.join(".", image.url.lstrip("/"))
    if os.path.exists(file_path):
        os.remove(file_path)

    db.delete(image)
    db.commit()
    return {"ok": True}