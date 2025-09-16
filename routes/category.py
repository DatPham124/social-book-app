from ..model import Category
from sqlmodel import Session, select
from fastapi import APIRouter, Depends, HTTPException
from common_lib.database import get_session_book_service

router = APIRouter(
    prefix="/category",
    tags=["category"]
)

# Create
@router.post("/add", response_model=Category)
def add_category(category: Category, session: Session = Depends(get_session_book_service)):
    # kiểm tra tên category đã tồn tại chưa
    existing_category = session.exec(select(Category).where(Category.name == category.name)).first()
    if existing_category:
        raise HTTPException(status_code=400, detail="Category already exists")

    session.add(category)
    session.commit()
    session.refresh(category)
    return category

# Read all
@router.get("/", response_model=list[Category])
def get_all(session: Session = Depends(get_session_book_service)):
    statement = select(Category)
    categories = session.exec(statement).all()

    if not categories:
        raise HTTPException(
            status_code=404,
            detail="No categories found"
        )
    
    return categories

# Read by id
@router.get("/{category_id}", response_model=Category)
def get_category(category_id: int, session: Session = Depends(get_session_book_service)):
    category = session.get(Category, category_id)

    if category is None:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )
    
    return category

# Update
@router.put("/update/{category_id}", response_model=Category)
def update_category(category_id: int, category_data: Category, session: Session = Depends(get_session_book_service)):
    category = session.get(Category, category_id)

    if category is None:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )
    
    # chỉ update field name
    if category_data.name is not None:
        category.name = category_data.name

    session.add(category)
    session.commit()
    session.refresh(category)

    return category

# Delete
@router.delete("/delete/{category_id}")
def delete_category(category_id: int, session: Session = Depends(get_session_book_service)):
    category = session.get(Category, category_id)

    if category is None:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )
    
    session.delete(category)
    session.commit()

    return {"msg": f"Category with id: {category_id} has been deleted"}
