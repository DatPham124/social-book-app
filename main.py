from fastapi import Depends, FastAPI
from common_lib.database import  engine_book_service
from .routes import books, author, category, bookclub
from sqlmodel import SQLModel, Table
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

@app.on_event("startup")
def on_startup():
    
    # with engine_book_service.begin() as conn:
    #     for table_name in ["bookclubcomment", "bookclubdiscussion", "bookclubbook", "bookclubmember", "bookclub", "bookclubmeeting"]:
    #         try:
    #             table = Table(table_name, SQLModel.metadata, autoload_with=engine_book_service)
    #             table.drop(engine_book_service)
    #             print(f"✅ Đã xóa bảng {table_name}")
    #         except Exception as e:
    #             print(f"⚠️ Không thể xóa bảng {table_name}: {e}")   
    
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
app.include_router(bookclub.router)
