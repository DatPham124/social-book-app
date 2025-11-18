from fastapi import Depends, FastAPI
from common_lib.database import  engine_book_service
from .routes import books, author, category, bookclub, buddyread, filter, stats, ai, challenge
from sqlmodel import SQLModel
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError

# 1. IMPORT TẤT CẢ CÁC MODEL TỪ FILE MODEL.PY CỦA BẠN
from .model import (
    Books, Authors, Category, BookCategoryLink,
    UserBookStatus, ReadingProgress, BookClub, BookClubMember,
    BookClubBook, BookClubDiscussion, BookClubComment, BookClubMeeting,
    InviteStatus, BookClubInvitation, BuddyRead, BuddyReadMember,
    BuddyReadComment, BuddyReadInvitation, AnnualChallenge
)

app = FastAPI()

@app.on_event("startup")
def on_startup():
    
    # try:
    #     print("--- (BOOK-SERVICE) Đang xóa tất cả các bảng... ---")
    #     SQLModel.metadata.drop_all(engine_book_service)
    #     print("✅ (BOOK-SERVICE) Đã xóa các bảng.")
    # except Exception as e:
    #     print(f"⚠️ Lỗi khi xóa bảng (có thể do CSDL): {e}")   
    
    # print("--- (BOOK-SERVICE) Đang tạo lại tất cả các bảng... ---")
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
app.include_router(buddyread.router)
app.include_router(filter.router)
app.include_router(stats.router)
app.include_router(ai.router)
app.include_router(challenge.router) 
