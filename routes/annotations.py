from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from sqlalchemy import and_

# Import các Model và Database dependency
from ..model import UserBookAnnotation
from common_lib.database import get_session_book_service

# Tạo Router riêng
router = APIRouter(
    prefix="/books", # Giữ prefix là /books hoặc tách riêng thành /annotations tùy bạn
    tags=["annotations"], # Gom nhóm trong Swagger UI
)

# --- API LẤY DANH SÁCH ANNOTATION ---
@router.get("/{book_id}/annotations/{user_id}", response_model=List[UserBookAnnotation])
def get_user_annotations(
    book_id: int, 
    user_id: int, 
    session: Session = Depends(get_session_book_service)
):
    """
    Lấy toàn bộ Highlight và Note của một user trong một cuốn sách.
    """
    statement = select(UserBookAnnotation).where(
        and_(
            UserBookAnnotation.book_id == book_id,
            UserBookAnnotation.user_id == user_id
        )
    )
    return session.exec(statement).all()

# --- API THÊM ANNOTATION ---
@router.post("/annotations/add", response_model=UserBookAnnotation)
def add_annotation(
    annotation: UserBookAnnotation, 
    session: Session = Depends(get_session_book_service)
):
    """
    Lưu một Highlight hoặc Note mới.
    """
    # Có thể thêm logic kiểm tra user_id, book_id tồn tại ở đây
    session.add(annotation)
    session.commit()
    session.refresh(annotation)
    return annotation

# --- API XÓA ANNOTATION ---
@router.delete("/annotations/delete/{annotation_id}")
def delete_annotation(
    annotation_id: int, 
    session: Session = Depends(get_session_book_service)
):
    """
    Xóa một Highlight hoặc Note dựa trên ID.
    """
    annotation = session.get(UserBookAnnotation, annotation_id)
    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")
    
    session.delete(annotation)
    session.commit()
    return {"message": "Deleted successfully"}