from fastapi import APIRouter, Depends, HTTPException, Body
from sqlmodel import Session, select, func
from typing import List, Optional
from sqlalchemy import or_ 
from sqlalchemy.sql.expression import desc
from pydantic import BaseModel
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os 
from pathlib import Path

from ..model import (
    UserBookStatus, Books, Category, BookCategoryLink, Authors, BookStatus
)
from common_lib.database import get_session_book_service

DOTENV_PATH = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(dotenv_path=DOTENV_PATH)

router = APIRouter(
    prefix="/ai/recommendations",
    tags=["AI & Recommendations"],
)
    
try:
    client = genai.Client() 
except Exception as e:
    print(f"Lỗi khởi tạo Gemini Client (hãy kiểm tra GEMINI_API_KEY): {e}")
    client = None

class FriendsRequest(BaseModel):
    user_id: int
    friend_ids: List[int]

class TopItem(BaseModel):
    name: str
    count: int

TASTE_PROFILE_FILTER = or_(
    UserBookStatus.status == BookStatus.read,
    UserBookStatus.status == BookStatus.to_read,
    UserBookStatus.status == BookStatus.currently_reading,
    UserBookStatus.is_favorite == True
)

# === CÁC HÀM PHỤ (HELPER FUNCTIONS) ===

def _get_genre_candidates(
    user_id: int, 
    session: Session, 
    limit: int = 10
) -> List[Books]:
    
    books_on_shelf_subquery = select(UserBookStatus.book_id).where(
        UserBookStatus.user_id == user_id
    )

    top_genres_statement = (
        select(Category.id, func.count(Category.id).label("genre_count"))
        .join(BookCategoryLink, Category.id == BookCategoryLink.category_id)
        .join(UserBookStatus, BookCategoryLink.book_id == UserBookStatus.book_id)
        .where(
            UserBookStatus.user_id == user_id,
            TASTE_PROFILE_FILTER 
        )
        .group_by(Category.id)
        .order_by(desc("genre_count"))
        .limit(3)
    )
    top_genres_results = session.exec(top_genres_statement).all()
    
    if not top_genres_results:
        return [] 

    top_genre_ids = [genre_id for genre_id, count in top_genres_results]

    recommend_statement = (
        select(Books)
        .join(BookCategoryLink, Books.id == BookCategoryLink.book_id)
        .where(
            BookCategoryLink.category_id.in_(top_genre_ids), 
            Books.id.not_in(books_on_shelf_subquery) 
        )
        .distinct(Books.id)
        .limit(limit)
    )
    
    books = session.exec(recommend_statement).all()
    return books

def _get_author_candidates(
    user_id: int, 
    session: Session, 
    limit: int = 10
) -> List[Books]:
    
    books_on_shelf_subquery = select(UserBookStatus.book_id).where(
        UserBookStatus.user_id == user_id
    )

    top_authors_statement = (
        select(Authors.id, func.count(Authors.id).label("author_count"))
        .join(Books, Authors.id == Books.authorID)
        .join(UserBookStatus, Books.id == UserBookStatus.book_id)
        .where(
            UserBookStatus.user_id == user_id,
            TASTE_PROFILE_FILTER,
            Authors.name != None
        )
        .group_by(Authors.id)
        .order_by(desc("author_count"))
        .limit(3)
    )
    top_authors_results = session.exec(top_authors_statement).all()

    if not top_authors_results:
        return []

    top_author_ids = [author_id for author_id, count in top_authors_results]

    recommend_statement = (
        select(Books)
        .where(
            Books.authorID.in_(top_author_ids),
            Books.id.not_in(books_on_shelf_subquery)
        )
        .distinct(Books.id)
        .limit(limit)
    )
    
    books = session.exec(recommend_statement).all()
    return books


# === CÁC API ROUTES ===

@router.get("/by-genre/{user_id}", response_model=List[Books])
def recommend_by_top_genres(
    user_id: int,
    session: Session = Depends(get_session_book_service),
    limit: int = 10
):
    return _get_genre_candidates(user_id, session, limit)

@router.get("/by-author/{user_id}", response_model=List[Books])
def recommend_by_top_authors(
    user_id: int,
    session: Session = Depends(get_session_book_service),
    limit: int = 10
):
    return _get_author_candidates(user_id, session, limit)

@router.post("/by-friends", response_model=List[Books])
def recommend_by_friends(
    request: FriendsRequest,
    session: Session = Depends(get_session_book_service),
    limit: int = 10
):
    if not request.friend_ids:
        return []
    books_on_shelf_subquery = select(UserBookStatus.book_id).where(
        UserBookStatus.user_id == request.user_id
    )
    popular_books_statement = (
        select(
            UserBookStatus.book_id, 
            func.count(UserBookStatus.book_id).label('popularity')
        )
        .where(
            UserBookStatus.user_id.in_(request.friend_ids),
            UserBookStatus.status == BookStatus.read,
            UserBookStatus.book_id.not_in(books_on_shelf_subquery)
        )
        .group_by(UserBookStatus.book_id)
        .order_by(desc('popularity'))
        .limit(limit)
    )
    popular_book_results = session.exec(popular_books_statement).all()
    popular_book_ids = [book_id for book_id, popularity in popular_book_results]
    if not popular_book_ids:
        return []
    books = session.exec(
        select(Books).where(Books.id.in_(popular_book_ids))
    ).all()
    return books

@router.get("/{user_id}", response_model=List[Books])
def recommend_by_ai(
    user_id: int,
    session: Session = Depends(get_session_book_service)
):
    if not client:
        raise HTTPException(status_code=500, detail="Dịch vụ AI chưa được cấu hình")

    profile_books_stmt = (
        select(Books.title, Authors.name.label("author_name"))
        .join(UserBookStatus, Books.id == UserBookStatus.book_id)
        .join(Authors, Books.authorID == Authors.id, isouter=True)
        .where(UserBookStatus.user_id == user_id, TASTE_PROFILE_FILTER)
        .order_by(UserBookStatus.updated_at.desc())
        .limit(10)
    )
    profile_books = session.exec(profile_books_stmt).all()
    
    if not profile_books:
        return [] 

    candidates_genre = _get_genre_candidates(user_id, session, limit=100)
    candidates_author = _get_author_candidates(user_id, session, limit=100)
    
    all_candidates = {book.id: book for book in candidates_genre}
    all_candidates.update({book.id: book for book in candidates_author})
    
    candidates_list = list(all_candidates.values())
    
    if not candidates_list:
        return []

    profile_prompt = "# HỒ SƠ NGƯỜI DÙNG (Sách người này quan tâm):\n"
    for title, author in profile_books:
        profile_prompt += f"- {title} (bởi {author or 'Không rõ'})\n"

    candidates_prompt = "\n# DANH SÁCH ỨNG CỬ VIÊN (Hãy chọn từ đây):\n"
    candidates_json_list = []
    for book in candidates_list:
        candidates_json_list.append({
            "id": book.id,
            "title": book.title,
            "description": (book.description or "")[:200] + "..."
        })
    
    candidates_prompt += json.dumps(candidates_json_list, indent=2, ensure_ascii=False)
    candidates_prompt += "\n"
    
    num_candidates = len(candidates_list)
    num_to_request = min(5, num_candidates) 

    task_prompt = f"""
# YÊU CẦU:
Dựa trên HỒ SƠ NGƯỜI DÙNG, hãy phân tích kỹ DANH SÁCH ỨNG CỬ VIÊN.
Chọn ra {num_to_request} cuốn sách (chính xác {num_to_request} cuốn) mà bạn tin rằng người dùng này sẽ thích nhất.

QUAN TRỌNG: Các ID sách trong kết quả trả về phải là **DUY NHẤT (unique)**.
Chỉ trả lời bằng một mảng JSON chứa {num_to_request} ID sách duy nhất (ví dụ: [12, 78, 45]).
Không giải thích gì thêm.
"""
    
    full_prompt = profile_prompt + candidates_prompt + task_prompt

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                temperature=0.2, 
                top_p=0.9
            ),
            contents=full_prompt 
        )
        
        response_text = response.text.strip().replace("`", "")
        
        try:
            if response_text.startswith("json"):
                response_text = response_text[4:].strip()
                
            recommended_ids = json.loads(response_text)
            if not isinstance(recommended_ids, list):
                raise ValueError("AI không trả về 1 danh sách")
        except Exception as json_err:
            print(f"Lỗi JSON parse: {json_err}. Response AI: {response_text}")
            raise HTTPException(status_code=500, detail="AI trả về định dạng không hợp lệ")

        if not recommended_ids:
            return []

        unique_ids = list(dict.fromkeys(recommended_ids))

        final_books = session.exec(
            select(Books).where(Books.id.in_(unique_ids))
        ).all()
        
        return final_books
        
    except Exception as e:
        print(f"Lỗi khi gọi Gemini: {str(e)}")
        try:
            print(f"Gemini response feedback: {response.prompt_feedback}")
        except:
            pass
        raise HTTPException(status_code=500, detail=f"AI không thể tạo gợi ý: {str(e)}")