from fastapi import Depends, FastAPI
from common_lib.database import  engine_book_service
from .routes import books
from sqlmodel import SQLModel, Session, select

app = FastAPI()

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine_book_service)


app.include_router(books.router)
