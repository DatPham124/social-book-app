from typing import List, Optional, Any
from sqlalchemy import extract, func, and_, Text
from fastapi import APIRouter, Depends, HTTPException, Query, Body
# 1. IMPORT THÊM 'delete'
from sqlmodel import Session, select, delete
from datetime import datetime, date
from google import genai
from google.genai import types
import os
from pydantic import BaseModel
from dotenv import load_dotenv
from pathlib import Path

from ..model import (
    BookStatus, Books, Category, ReadingProgress, UserBookStatus, BookCategoryLink, Authors,
    AiSummaryCache, BuddyRead, BuddyReadMember, BuddyReadComment, BuddyReadInvitation,
    BookClubBook, BookAudio
)
from common_lib.database import get_session_book_service

load_dotenv()

router = APIRouter(
    prefix="/books",
    tags=["books"],
)
    
client = genai.Client()

class SummaryResponse(BaseModel):
    summary_text: str

# === BOOK ROUTES ===

@router.get("/search", response_model=list[Books])
def search_books(
    q: str = Query(..., min_length=1, description="Từ khóa tìm kiếm theo tiêu đề sách"),
    limit: int = Query(10, ge=1, le=50),
    session: Session = Depends(get_session_book_service)
):
    query = (
        select(Books)
        .where(
            (Books.title.ilike(f"%{q}%"))
        )
        .limit(limit)
    )
    results = session.exec(query).all()
    
    if not results:
        return []
    
    return results  

@router.post('/add', response_model=Books)
def add_book(book: Books, session: Session = Depends(get_session_book_service)):
    session.add(book)
    session.commit()
    session.refresh(book)
    return book


@router.get("/", response_model=list[Books])
def get_all_books(session: Session = Depends(get_session_book_service)):
    statement = select(Books)
    books = session.exec(statement).all()
    return books


@router.get("/{book_id}/ai-summary", response_model=SummaryResponse)
def get_ai_summary(
    book_id: int, 
    session: Session = Depends(get_session_book_service)
):
    
    cached_summary = session.get(AiSummaryCache, book_id)
    if cached_summary:
        return SummaryResponse(summary_text=cached_summary.summary_text)

    if not client:
        raise HTTPException(status_code=500, detail="Dịch vụ AI chưa được cấu hình (thiếu API Key)")

    statement = (
        select(Books, Authors.name.label("author_name"))
        .join(Authors, Authors.id == Books.authorID, isouter=True) 
        .where(Books.id == book_id)
    )
    result = session.exec(statement).first()

    if not result:
        raise HTTPException(status_code=404, detail="Không tìm thấy sách")

    book, author_name = result
    
    book_title = book.title
    book_author = author_name or "Không rõ tác giả"
    book_description = book.description
    
    system_instruction = "Bạn là một người viết lời giới thiệu sách chuyên nghiệp (blurb writer), chuyên khơi gợi sự tò mò của người đọc."
    
    prompt = ""
    if book_description:
        prompt = f"""
        Dựa trên thông tin sau:
        Tên sách: '{book_title}'
        Tác giả: '{book_author}'
        Mô tả: '{book_description}'
        
        Nhiệm vụ: Hãy viết một đoạn tóm tắt (khoảng 2-3 câu) thật lôi cuốn để khiến người đọc ham muốn đọc cuốn sách này.
        Yêu cầu:
        1. Không dùng gạch đầu dòng.
        2. Không tiết lộ (spoil) chi tiết quan trọng của cốt truyện.
        3. Hãy kết thúc bằng một câu hỏi hoặc một lời hứa hẹn đầy kịch tính để khơi gợi sự tò mò.
        """
    else:
        prompt = f"""
        Bạn có biết về cuốn sách '{book_title}' của tác giả '{book_author}'.
        
        Nhiệm vụ: Hãy viết một đoạn tóm tắt (khoảng 2-3 câu) thật lôi cuốn để khiến người đọc ham muốn đọc cuốn sách này.
        Yêu cầu:
        1. Không dùng gạch đầu dòng.
        2. Không tiết lộ (spoil) chi tiết quan trọng của cốt truyện.
        3. Hãy kết thúc bằng một câu hỏi hoặc một lời hứa hẹn đầy kịch tính để khơi gợi sự tò mò.
        """

    try:
        generate_content_config = types.GenerateContentConfig(
        temperature=0.5,
        top_p=0.9,
        thinking_config = types.ThinkingConfig(
            thinking_budget=0,
        ),
    )
        
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            config=generate_content_config,
            contents=[prompt] 
        )
        
        summary_text = response.text.strip() 

        new_cache_entry = AiSummaryCache(
            book_id=book_id,
            summary_text=summary_text
        )
        session.add(new_cache_entry)
        session.commit()

        return SummaryResponse(summary_text=summary_text)
        
    except Exception as e:
        print(f"Lỗi khi gọi Gemini: {str(e)}")
        try:
            print(f"Gemini response feedback: {response.prompt_feedback}")
        except:
            pass
        raise HTTPException(status_code=500, detail=f"AI không thể tạo tóm tắt: {str(e)}")
    
@router.delete("/{book_id}/ai-summary")
def delete_ai_summary(
    book_id: int, 
    session: Session = Depends(get_session_book_service)
):    
    cached_summary = session.get(AiSummaryCache, book_id)
    
    if not cached_summary:
        raise HTTPException(status_code=404, detail="Không tìm thấy tóm tắt (cache) để xóa.")
    
    session.delete(cached_summary)
    session.commit()
    
    return {"message": f"Đã xóa tóm tắt AI của sách (ID: {book_id}) thành công."}
    
@router.get("/{book_id}", response_model=Books)
def get_book_by_id(book_id: int, session: Session = Depends(get_session_book_service)):
    book = session.get(Books, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    return book

@router.post("/{book_id}/audio/add")
def add_audio_chapter(
    book_id: int,
    title: str = Body(...),
    file_url: str = Body(...),
    order: int = Body(0),
    session: Session = Depends(get_session_book_service)
):
    audio = BookAudio(book_id=book_id, title=title, file_url=file_url, order=order)
    session.add(audio)
    session.commit()
    return audio

# API LẤY CHI TIẾT SÁCH KÈM AUDIO
@router.get("/{book_id}/details") 
def get_book_with_audios(
    book_id: int,
    session: Session = Depends(get_session_book_service)
):
    book = session.get(Books, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Lấy danh sách audio
    audios = session.exec(
        select(BookAudio).where(BookAudio.book_id == book_id).order_by(BookAudio.order)
    ).all()
    
    # Trả về dạng Dict
    return {
        **book.model_dump(),
        "audios": audios
    }

@router.put('/update/{book_id}', response_model=Books)
def update_book(book_id: int, book_data: Books, session: Session = Depends(get_session_book_service)):
    book = session.get(Books, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail='No book found')
    
    update_fields = ["title", "description", "cover_url", "published_date", "language", "authorID", "page_count", "file_url"]
    for field in update_fields:
        value = getattr(book_data, field)
        if value is not None:
            setattr(book, field, value)

    session.add(book)
    session.commit()
    session.refresh(book)
    
    cached_summary = session.get(AiSummaryCache, book_id)
    if cached_summary:
        session.delete(cached_summary)
        session.commit() 
    return book


@router.delete('/delete/{book_id}')
def delete_book_by_id(book_id: int, session: Session = Depends(get_session_book_service)):  
    
    book = session.get(Books, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
        
    buddy_reads_to_delete = session.exec(
        select(BuddyRead).where(BuddyRead.book_id == book_id)
    ).all()
    
    if buddy_reads_to_delete:
        buddy_read_ids = [br.id for br in buddy_reads_to_delete if br.id is not None]
        
        if buddy_read_ids:
            session.exec(
                delete(BuddyReadComment).where(BuddyReadComment.buddy_read_id.in_(buddy_read_ids))
            )
            session.exec(
                delete(BuddyReadInvitation).where(BuddyReadInvitation.buddy_read_id.in_(buddy_read_ids))
            )
            session.exec(
                delete(BuddyReadMember).where(BuddyReadMember.buddy_read_id.in_(buddy_read_ids))
            )
        
        for br in buddy_reads_to_delete:
            session.delete(br)


    # Xóa link Thể loại
    session.exec(delete(BookCategoryLink).where(BookCategoryLink.book_id == book_id))
    
    # Xóa trạng thái của User (Kệ sách)
    session.exec(delete(UserBookStatus).where(UserBookStatus.book_id == book_id))
    
    # Xóa tiến độ đọc
    session.exec(delete(ReadingProgress).where(ReadingProgress.book_id == book_id))
    
    # Xóa link Sách của CLB
    session.exec(delete(BookClubBook).where(BookClubBook.book_id == book_id))
    
    # Xóa Tóm tắt AI (Cache)
    cached_summary = session.get(AiSummaryCache, book_id)
    if cached_summary:
        session.delete(cached_summary)
    
    # 3. XÓA "CHA" (Sách)
    session.delete(book)
    
    session.commit()
    
    return {"message": f"Book with id {book_id} and all related data has been deleted"}

# === USER BOOK STATUS ROUTES ===
@router.get('/status/all', response_model=list[UserBookStatus])
def get_all_status_books(session: Session = Depends(get_session_book_service)):
    statement = select(UserBookStatus)
    status = session.exec(statement).all()
    return status

@router.get('/favorite/{user_id}', response_model=list[UserBookStatus])
def get_favorite_book_by_user(user_id: int, session: Session = Depends(get_session_book_service)):
    statement = select(UserBookStatus).where(
        and_(
            UserBookStatus.user_id == user_id,
            UserBookStatus.is_favorite == True
        )
    )
    
    results = session.exec(statement).all()
    return results

@router.put('/favorite/update/{book_id}/{user_id}')
def change_favorite_stage(book_id: int, user_id: int, session: Session = Depends(get_session_book_service)):
    statement = select(UserBookStatus).where(
        UserBookStatus.user_id == user_id,
        UserBookStatus.book_id == book_id
    )
    
    user_book = session.exec(statement).first()
    
    if not user_book:
        user_book = UserBookStatus(
            user_id=user_id,
            book_id=book_id,
            status=BookStatus.to_read 
        )
    
    user_book.is_favorite = not user_book.is_favorite
    session.add(user_book)
    session.commit()
    session.refresh(user_book)
    
    return {"book_id": book_id, "user_id": user_id, "is_favorite": user_book.is_favorite}


@router.post('/status/add')
def add_book_status(status_change: str, book_id: int, user_id: int, session: Session = Depends(get_session_book_service)):
    valid_status = ["to_read", "currently_reading", "read", "dnf"]
    if status_change not in valid_status:
        raise HTTPException(status_code=400, detail="Trạng thái không hợp lệ")

    new_status = UserBookStatus(
        user_id=user_id,
        book_id=book_id,
        status=status_change
    )
    session.add(new_status)
    session.commit()
    session.refresh(new_status)
    return {"message": "Book status added successfully"}

@router.get('/status/book/{user_id}', response_model=list[UserBookStatus])
def get_book_by_status_and_userID(
    status: str,
    user_id: int,  
    session: Session = Depends(get_session_book_service)
):
    valid_status = ["to_read", "currently_reading", "read", "dnf"]
    if status not in valid_status:
        raise HTTPException(
            status_code=400,
            detail=f"Trạng thái không hợp lệ. Hợp lệ: {', '.join(valid_status)}"
        )

    statement = select(UserBookStatus).where(
        and_(
            UserBookStatus.status == status,
            UserBookStatus.user_id == user_id
        )
    )
    results = session.exec(statement).all()

    return results


@router.put('/{book_id}/status')
def update_user_book_status(
    book_id: int,
    user_id: int,
    status: str,
    session: Session = Depends(get_session_book_service)
):
    valid_status = ["to_read", "currently_reading", "read", "dnf"]
    if status not in valid_status:
        raise HTTPException(status_code=400, detail="Trạng thái không hợp lệ")

    statement = select(UserBookStatus).where(
        and_(
            UserBookStatus.book_id == book_id,
            UserBookStatus.user_id == user_id
        )
    )
    book_status = session.exec(statement).first()

    if not book_status:
        book_status = UserBookStatus(
            user_id=user_id,
            book_id=book_id,
            status=status
        )
    else:
        book_status.status = status
        book_status.updated_at = datetime.utcnow()
    
    session.add(book_status)
    session.commit()
    session.refresh(book_status)
    return {"message": "✅ Book status updated", "status": book_status.status}


@router.get("/explore/{user_id}")
def get_explore_books(
    user_id: int,
    offset: int = Query(0, ge=0),
    limit: int = Query(10, le=50),
    session: Session = Depends(get_session_book_service)
):
    subquery = select(UserBookStatus.book_id).where(UserBookStatus.user_id == user_id)

    statement = (
        select(Books)
        .where(Books.id.not_in(subquery))
        .offset(offset)
        .limit(limit)
    )

    books = session.exec(statement).all()

    results = []
    for book in books:
        category_stmt = (
            select(Category.name)
            .join(BookCategoryLink, BookCategoryLink.category_id == Category.id)
            .where(BookCategoryLink.book_id == book.id)
        )
        category_names = session.exec(category_stmt).all()
        
        results.append({
            "id": book.id,
            "title": book.title,
            "description": book.description,
            "cover_url": book.cover_url,
            "published_date": book.published_date,
            "language": book.language,
            "authorID": book.authorID,
            "page_count": book.page_count,
            "categories": category_names,  
            "status": "to_read"
        })
    
    return results


@router.get("/{book_id}/categories", response_model=List[Category])
def get_book_categories(book_id: int, session: Session = Depends(get_session_book_service)):
    book = session.get(Books, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    return book.categories

@router.get("/reading-progress/{user_id}/{book_id}", response_model=Any)
def get_reading_progress(
    user_id: int,
    book_id: int,
    session: Session = Depends(get_session_book_service)
):
    statement = select(ReadingProgress).where(
        and_(
            ReadingProgress.user_id == user_id,
            ReadingProgress.book_id == book_id
        )
    )
    progress = session.exec(statement).first()
    
    if not progress:
        book = session.get(Books, book_id)
        return {
            "user_id": user_id,
            "book_id": book_id,
            "current_page": 0,
            "total_pages": book.page_count if book else 0
        }
    
    return progress

@router.put("/reading-progress/{user_id}/{book_id}", response_model=ReadingProgress)
def update_reading_progress(
    user_id: int,
    book_id: int,
    current_page_from_user: int,
    session: Session = Depends(get_session_book_service)
):
    
    book = session.get(Books, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    if book.page_count and current_page_from_user > book.page_count:
        raise HTTPException(status_code=400, detail="Số trang vượt quá số trang thực tế")

    statement = select(ReadingProgress).where(
        and_(
            ReadingProgress.user_id == user_id,
            ReadingProgress.book_id == book_id
        )
    )
    progress = session.exec(statement).first()

    if not progress:
        progress = ReadingProgress(
            user_id=user_id,
            book_id=book_id,
            current_page=current_page_from_user    
        )
    else:
        progress.current_page = current_page_from_user
        
    session.add(progress)
    session.commit()
    session.refresh(progress)
    
    return progress

@router.get("/status/{user_id}/{book_id}", response_model=Optional[UserBookStatus])
def get_book_status(user_id: int, book_id: int, session: Session = Depends(get_session_book_service)):
    status = session.exec(
        select(UserBookStatus).where(
            UserBookStatus.user_id == user_id,
            UserBookStatus.book_id == book_id
        )
    ).first()

    if not status:
        return None 

    return status

@router.delete("/status/{user_id}/{book_id}")
def delete_book_status(user_id: int, book_id: int, session: Session = Depends(get_session_book_service)):
    status_record = session.exec(
        select(UserBookStatus).where(
            UserBookStatus.user_id == user_id,
            UserBookStatus.book_id == book_id
        )
    ).first()

    if not status_record:
        raise HTTPException(status_code=404, detail="Không tìm thấy trạng thái sách")

    session.delete(status_record)
    session.commit()

    return {"message": "Xóa trạng thái thành công"}


@router.get("/stats/counts/{user_id}")
def get_user_read_counts(
    user_id: int,
    session: Session = Depends(get_session_book_service)
):
    
    total_read_stmt = (
        select(func.count(UserBookStatus.id))
        .where(
            UserBookStatus.user_id == user_id,
            UserBookStatus.status == BookStatus.read
        )
    )
    total_read = session.exec(total_read_stmt).one_or_none() or 0

    current_year = datetime.utcnow().year
    year_read_stmt = (
        select(func.count(UserBookStatus.id))
        .where(
            UserBookStatus.user_id == user_id,
            UserBookStatus.status == BookStatus.read,
            extract('year', UserBookStatus.updated_at) == current_year
        )
    )
    read_this_year = session.exec(year_read_stmt).one_or_none() or 0

    return {
        "total_read": total_read,
        "read_this_year": read_this_year
    }


@router.get("/feed/recent-status", response_model=List[UserBookStatus])
def get_recent_status_feed(
    session: Session = Depends(get_session_book_service),
    limit: int = 50 
):
    statement = (
        select(UserBookStatus)
        .where(UserBookStatus.status.in_([BookStatus.read, BookStatus.currently_reading]))
        .order_by(UserBookStatus.updated_at.desc())
        .limit(limit)
    )
    activities = session.exec(statement).all()
    return activities

class DateUpdateRequest(BaseModel):
    start_date: Optional[date] = None
    finish_date: Optional[date] = None

@router.put("/status/dates/{user_id}/{book_id}", response_model=UserBookStatus)
def update_reading_dates(
    user_id: int,
    book_id: int,
    dates: DateUpdateRequest, 
    session: Session = Depends(get_session_book_service)
):
    
    statement = select(UserBookStatus).where(
        UserBookStatus.user_id == user_id,
        UserBookStatus.book_id == book_id
    )
    status_record = session.exec(statement).first()

    if not status_record:
        status_record = UserBookStatus(
            user_id=user_id,
            book_id=book_id,
            status=BookStatus.to_read 
        )
        
    status_record.start_date = dates.start_date
    status_record.finish_date = dates.finish_date
    status_record.updated_at = datetime.utcnow() 
    
    session.add(status_record)
    session.commit()
    session.refresh(status_record)
    
    return status_record