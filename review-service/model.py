from datetime import date, datetime 
from typing import Optional
from sqlalchemy import Text
from sqlmodel import SQLModel, Field, UniqueConstraint


class Reviews(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("user_id", "book_id"),) 
    id: Optional[int] = Field(default=None, primary_key= True)
    user_id: int = Field(nullable=False, index=True)
    book_id: int = Field(nullable=False, index=True)
    rating: float = Field(nullable=False, index=True)
    content: Optional[str] = Field(sa_column=Field(default=None, sa_column=Text()))    
    
    created_at: datetime = Field(default_factory=datetime.utcnow) 

class Likes(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("user_id", "review_id"),) 
    id: Optional[int] = Field(default=None, primary_key= True)
    user_id: int = Field(nullable=False, index=True)
    review_id: int = Field(nullable=False, index=True, foreign_key="reviews.id")
    created_at: date = Field(default_factory=date)

class Comments(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    review_id: int = Field(nullable=False, index=True, foreign_key="reviews.id")
    user_id: int = Field(nullable=False, index=True)
    content: str = Field(nullable=False)
    update_at: date = Field(default_factory=date)
    


