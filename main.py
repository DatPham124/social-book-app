from fastapi import FastAPI
from sqlmodel import SQLModel
from common_lib.database import  engine_review_service
from fastapi.middleware.cors import CORSMiddleware
from .routes import review, like, comment
app = FastAPI()

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine_review_service)
    
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(review.router)
app.include_router(like.router)
app.include_router(comment.router)