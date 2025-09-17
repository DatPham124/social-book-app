from fastapi import FastAPI
from sqlmodel import SQLModel
from common_lib.database import  engine_review_service
from .routes import review, like
app = FastAPI()

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine_review_service)

app.include_router(review.router)
app.include_router(like.router)