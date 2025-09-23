from datetime import date
from typing import Optional
from enum import Enum  # Python Enum
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Enum as SqlEnum, UniqueConstraint


class Books(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True, nullable=False)
    description: Optional[str] = None
    cover_url: Optional[str] = None
    published_date: Optional[date] = None
    language: Optional[str] = None
    authorID: Optional[int] = Field(foreign_key="authors.id")
    categoryID: Optional[int] = Field(foreign_key="category.id")
    created_at: date = Field(default_factory=date.today)


class Authors(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    bio: Optional[str] = None
    birth_date: Optional[date] = None


class Category(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)


class BookStatus(str, Enum):  # dùng Python Enum
    to_read = "to_read"
    currently_reading = "currently_reading"
    read = "read"
    did_not_finish = "DNF"


class UserBookStatus(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, nullable=False)
    book_id: int = Field(foreign_key="books.id", nullable=False)
    status: BookStatus = Field(
        sa_column=Column(SqlEnum(BookStatus), nullable=False, default=BookStatus.to_read)
    )
    updated_at: date = Field(default_factory=date.today)


class ReadingProgress(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, nullable=False)
    book_id: int = Field(foreign_key="books.id", nullable=False)
    current_page: int = Field(default=0, nullable=False)
    total_pages: int = Field(default=0, nullable=False)
    updated_at: date = Field(default_factory=date.today)

    __table_args__ = (
        UniqueConstraint('user_id', 'book_id', name='uix_user_book'),
    )
