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
    
class ChatMessageHistory(BaseModel):
    role: str # "user" hoặc "model"
    message: str

class CharacterChatRequest(BaseModel):
    book_id: int
    character_name: str
    user_message: str
    history: List[ChatMessageHistory] = []

class CharacterChatResponse(BaseModel):
    reply: str

class CharacterListResponse(BaseModel):
    characters: List[str]
    
# === CHỨC NĂNG CHAT NHÂN VẬT (ĐÃ NÂNG CẤP XỬ LÝ BIÊN) ===

@router.get("/characters/{book_id}", response_model=CharacterListResponse)
def get_book_characters(
    book_id: int,
    session: Session = Depends(get_session_book_service)
):
    if not client:
        raise HTTPException(status_code=500, detail="Dịch vụ AI chưa được cấu hình")

    book_stmt = (
        select(Books.title, Authors.name.label("author_name"))
        .join(Authors, Books.authorID == Authors.id, isouter=True)
        .where(Books.id == book_id)
    )
    result = session.exec(book_stmt).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Không tìm thấy sách")
        
    book_title, author_name = result
    
    # --- SỬA PROMPT: Xử lý sách không có nhân vật ---
    prompt = f"""
    Phân tích cuốn sách: "{book_title}" của tác giả "{author_name}".
    
    Nhiệm vụ: Hãy liệt kê 5 "vai diễn" (personas) mà người đọc có thể trò chuyện cùng.
    
    QUY TẮC XỬ LÝ:
    1. Nếu là Sách Truyện/Tiểu thuyết: Liệt kê các nhân vật chính (Ví dụ: Harry Potter, Ron).
    2. Nếu là Sách Self-help/Kinh doanh/Học thuật (Ví dụ: Atomic Habits): Liệt kê Tên Tác Giả (Ví dụ: James Clear) hoặc các khái niệm được nhân cách hóa (Ví dụ: "Người Cố Vấn", "Chuyên gia Thói quen").
    3. Nếu là Sách Nấu ăn: Liệt kê "Bếp trưởng" hoặc Tác giả.
    4. Nếu không xác định được ai: Hãy trả về ["Tác giả", "Cuốn sách này"].
    
    YÊU CẦU ĐẦU RA:
    Chỉ trả về một mảng JSON chứa danh sách tên (String).
    Ví dụ: ["James Clear", "Huấn luyện viên thói quen"]
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-lite",
            config=types.GenerateContentConfig(
                temperature=0.1, 
                response_mime_type="application/json",
                safety_settings=[
                    types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
                    types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
                    types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
                    types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
                ]
            ),
            contents=prompt
        )
        
        if not response.text:
             return CharacterListResponse(characters=["Tác giả", "Người dẫn chuyện"])

        characters = json.loads(response.text)
        
        if isinstance(characters, dict) and "characters" in characters:
             return CharacterListResponse(characters=characters["characters"])
        elif isinstance(characters, list):
             return CharacterListResponse(characters=characters)
        else:
             return CharacterListResponse(characters=["Tác giả"])
             
    except Exception as e:
        print(f"Lỗi lấy nhân vật: {e}")
        # Luôn trả về ít nhất một lựa chọn để UI không trống
        return CharacterListResponse(characters=["Tác giả"])


# 2. API CHAT NHÂN VẬT (Đã sửa prompt để nhập vai linh hoạt)
@router.post("/chat-character", response_model=CharacterChatResponse)
def chat_with_character(
    request: CharacterChatRequest,
    session: Session = Depends(get_session_book_service)
):
    if not client:
        raise HTTPException(status_code=500, detail="Dịch vụ AI chưa được cấu hình")

    # 1. Lấy thông tin sách
    book_stmt = (
        select(Books, Authors.name.label("author_name"))
        .join(Authors, Books.authorID == Authors.id, isouter=True)
        .where(Books.id == request.book_id)
    )
    result = session.exec(book_stmt).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Không tìm thấy sách")
        
    book, author_name = result
    
    # 2. Tạo "System Instruction" (Lời nhắc hệ thống) - Định nghĩa vai trò
    system_prompt = f"""
    HÃY NHẬP VAI (ROLEPLAY):
    Tên bạn là: **{request.character_name}**.
    Bạn là một nhân vật trong cuốn sách: **"{book.title}"** của tác giả **"{author_name or 'Unknown'}"**.
    Bối cảnh/Mô tả sách: "{book.description or 'Không có mô tả'}"

    NHIỆM VỤ:
    1. **Giọng điệu:** Hãy giữ đúng tính cách của nhân vật (ví dụ: Hermione thì thông thái, Voldemort thì kiêu ngạo).
    2. **Tự nhiên:** Đừng cứng nhắc. Hãy thoải mái bộc lộ cảm xúc, suy nghĩ, hạn chế đặt câu hỏi ngược lại nếu không cần thiết.
    3. **Đời thường:** Trả lời ngắn gọn (dưới 100 từ), đi thẳng vào vấn đề, không cần chào hỏi quá trang trọng nếu không cần thiết.
    4. **Nhập tâm:** Tuyệt đối không bao giờ nói "Tôi là AI" hay "Tôi là mô hình ngôn ngữ". Hãy sống trọn vẹn vai diễn của mình.
    """

    # 3. Xây dựng chuỗi hội thoại (History) cho Gemini
    chat_contents = []
    
    # Thêm lịch sử cũ (nếu có)
    if request.history:
        for msg in request.history:
            # Map role từ frontend ("user"/"ai") sang Gemini ("user"/"model")
            gemini_role = "user" if msg.role == "user" else "model"
            chat_contents.append(
                types.Content(role=gemini_role, parts=[types.Part(text=msg.message)])
            )
    
    # Thêm tin nhắn mới nhất của user
    chat_contents.append(
        types.Content(role="user", parts=[types.Part(text=request.user_message)])
    )

    # 4. Gọi Gemini
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-lite",
            config=types.GenerateContentConfig(
                temperature=0.8, 
                system_instruction=system_prompt, # Đưa roleplay vào system instruction
                safety_settings=[
                    types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
                    types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
                    types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
                    types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
                ]
            ),
            contents=chat_contents # Gửi toàn bộ lịch sử
        )
        
        if response.text:
             return CharacterChatResponse(reply=response.text.strip())
        else:
             print(f"Gemini returned empty text. Safety ratings: {response.prompt_feedback}")
             return CharacterChatResponse(reply="...(Nhân vật đang trầm tư hoặc không muốn trả lời câu hỏi này)...")

    except Exception as e:
        print(f"Lỗi Chat AI: {e}")
        return CharacterChatResponse(reply="(Hệ thống: Có lỗi kết nối với nhân vật. Vui lòng thử lại sau.)")