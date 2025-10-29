from datetime import date, datetime
from typing import Optional, List
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, Enum as SqlEnum, UniqueConstraint


class BookCategoryLink(SQLModel, table=True):
    book_id: int = Field(foreign_key="books.id", primary_key=True)
    category_id: int = Field(foreign_key="category.id", primary_key=True)


class Category(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    books: List["Books"] = Relationship(back_populates="categories", link_model=BookCategoryLink)


class Books(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True, nullable=False)
    description: Optional[str] = None
    cover_url: Optional[str] = None
    published_date: Optional[date] = None
    language: Optional[str] = None
    page_count: Optional[int] = None  
    authorID: Optional[int] = Field(foreign_key="authors.id")
    created_at: date = Field(default_factory=date.today)
    categories: List[Category] = Relationship(back_populates="books", link_model=BookCategoryLink)

class Authors(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)

class BookStatus(str, Enum):  # dùng Python Enum
    to_read = "to_read"
    currently_reading = "currently_reading"
    read = "read"
    did_not_finish = "dnf"
    rm_book = "rm_book"


class UserBookStatus(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, nullable=False)
    book_id: int = Field(foreign_key="books.id", nullable=False)
    status: BookStatus = Field(
        sa_column=Column(SqlEnum(BookStatus), nullable=False, default=BookStatus.to_read)
    )
    start_date: Optional[date] = None 
    finish_date: Optional[date] = None
    updated_at: date = Field(default_factory=date.today)
    is_favorite: bool = Field(default=False, nullable=False)
    
class ReadingProgress(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, nullable=False)
    book_id: int = Field(foreign_key="books.id", nullable=False)
    current_page: int = Field(default=0, nullable=False)
    updated_at: date = Field(default_factory=date.today)

    __table_args__ = (
        UniqueConstraint('user_id', 'book_id', name='uix_user_book'),
    )
    
class BookClub(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, nullable=False)
    description: Optional[str] = Field(default=None)
    creator_id: int = Field(index=True, nullable=False)
    is_public: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    avatar_url: Optional[str] = None 

    members: List["BookClubMember"] = Relationship(back_populates="club")
    books: List["BookClubBook"] = Relationship(back_populates="club")
    discussions: List["BookClubDiscussion"] = Relationship(back_populates="club")

class BookClubMember(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    club_id: int = Field(foreign_key="bookclub.id", nullable=False)
    user_id: int = Field(index=True, nullable=False)
    role: str = Field(default="member")  # "host", "member"
    joined_at: datetime = Field(default_factory=datetime.utcnow)

    club: Optional[BookClub] = Relationship(back_populates="members")

    __table_args__ = (
        UniqueConstraint("club_id", "user_id", name="uix_club_user"),
    )

class BookClubBook(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    club_id: int = Field(foreign_key="bookclub.id", nullable=False)
    book_id: int = Field(foreign_key="books.id", nullable=False)
    status: str = Field(default="reading")  # "reading", "finished", "suggested"
    added_at: datetime = Field(default_factory=datetime.utcnow)

    club: Optional[BookClub] = Relationship(back_populates="books")

    __table_args__ = (
        UniqueConstraint("club_id", "book_id", name="uix_club_book"),
    )

class BookClubDiscussion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    club_id: int = Field(foreign_key="bookclub.id", nullable=False)
    user_id: int = Field(index=True, nullable=False)
    title: str = Field(nullable=False)
    content: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    club: Optional[BookClub] = Relationship(back_populates="discussions")
    comments: List["BookClubComment"] = Relationship(back_populates="discussion")

class BookClubComment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    discussion_id: int = Field(foreign_key="bookclubdiscussion.id", nullable=False)
    user_id: int = Field(index=True, nullable=False)
    content: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    discussion: Optional[BookClubDiscussion] = Relationship(back_populates="comments")

class BookClubMeeting(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    club_id: int = Field(foreign_key="bookclub.id", nullable=False)
    title: str = Field(nullable=False)
    date: datetime = Field(nullable=False)
    status: str = Field(default="upcoming")  # upcoming, past
    created_at: datetime = Field(default_factory=datetime.utcnow)
