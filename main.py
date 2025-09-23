from fastapi import Depends, FastAPI
from common_lib.database import  engine_book_service
from .routes import books, author, category
from sqlmodel import SQLModel, Session, select
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

@app.on_event("startup")
def on_startup():


    SQLModel.metadata.create_all(engine_book_service)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(books.router)
app.include_router(author.router)
app.include_router(category.router)
