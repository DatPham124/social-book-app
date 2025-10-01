from ..model import BookCategoryLink, Books, Category
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

@router.post(
    "/book-category-link/add", 
    response_model=BookCategoryLink,
)
def add_book_to_category(
    link_data: BookCategoryLink, 
    session: Session = Depends(get_session_book_service)
):
    # 1. Kiểm tra sự tồn tại của Sách và Danh mục
    book_exists = session.get(Books, link_data.book_id)
    category_exists = session.get(Category, link_data.category_id)

    if not book_exists:
        raise HTTPException(
            status_code=404, 
            detail=f"Book with id: {link_data.book_id} not found"
        )
    if not category_exists:
        raise HTTPException(
            status_code=404, 
            detail=f"Category with id: {link_data.category_id} not found"
        )

    # 2. Kiểm tra liên kết đã tồn tại chưa
    statement = select(BookCategoryLink).where(
        BookCategoryLink.book_id == link_data.book_id,
        BookCategoryLink.category_id == link_data.category_id
    )
    existing_link = session.exec(statement).first()

    if existing_link:
        raise HTTPException(
            status_code=400, 
            detail="Book is already linked to this category"
        )

    # 3. Tạo và thêm liên kết
    new_link = BookCategoryLink(**link_data.model_dump())
    
    session.add(new_link)
    session.commit()
    session.refresh(new_link)

    return new_link


@router.delete("/book-category-link/remove")
def remove_book_from_category(
    book_id: int, 
    category_id: int, 
    session: Session = Depends(get_session_book_service)
):
    # 1. Tìm liên kết
    statement = select(BookCategoryLink).where(
        BookCategoryLink.book_id == book_id,
        BookCategoryLink.category_id == category_id
    )
    link_to_delete = session.exec(statement).first()

    if link_to_delete is None:
        raise HTTPException(
            status_code=404,
            detail=f"Link between Book ID {book_id} and Category ID {category_id} not found"
        )
    
    # 2. Xóa liên kết
    session.delete(link_to_delete)
    session.commit()

    return {
        "msg": f"Link between Book ID {book_id} and Category ID {category_id} has been removed"
    }
    
    
@router.get("/book-category-link/", response_model=list[BookCategoryLink])
def get_all_links(session: Session = Depends(get_session_book_service)):
    links = session.exec(select(BookCategoryLink)).all()
    # Nếu không muốn trả về [] cho danh sách trống, bạn có thể raise HTTPException 404
    return links


@router.get("/book-category-link/book/{book_id}", response_model=list[BookCategoryLink])
def get_links_by_book(book_id: int, session: Session = Depends(get_session_book_service)):
    links = session.exec(
        select(BookCategoryLink).where(BookCategoryLink.book_id == book_id)
    ).all()

    if not links:
        raise HTTPException(
            status_code=404,
            detail=f"No categories linked to Book ID: {book_id}"
        )
    return links