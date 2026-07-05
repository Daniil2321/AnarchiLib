# database.py
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Mapped, mapped_column
from datetime import datetime
from typing import List

# ----- Базовый класс -----
Base = declarative_base()

# ----- Модель акции -----
class Action(Base):
    __tablename__ = 'actions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    date: Mapped[str] = mapped_column(String, nullable=False)
    location: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default='planned')  # planned, ongoing, completed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    images: Mapped[List["ActionImage"]] = relationship(
        back_populates='action',
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f"<Action {self.id}: {self.title}>"

class ActionImage(Base):
    __tablename__ = 'action_images'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)   # полный путь (например, /static/uploads/img.jpg)
    action_id: Mapped[int] = mapped_column(Integer, ForeignKey('actions.id'))

    action: Mapped["Action"] = relationship(back_populates='images')

    def __repr__(self):
        return f"<ActionImage {self.id}: {self.filename}>"


# ----- Настройка подключения -----
DATABASE_URL = "sqlite:///./anarchist.db"
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # нужно для SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ----- Функция для создания таблиц -----
def create_tables():
    Base.metadata.create_all(bind=engine)
