from fastapi import FastAPI
from common_lib.database import  engine_book_service
from sqlmodel import SQLModel, Session, select

app = FastAPI()



