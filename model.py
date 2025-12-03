from datetime import date, datetime
from typing import Optional, List
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, Enum as SqlEnum, Text, UniqueConstraint


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
    file_url: Optional[str] = None

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
    updated_at: datetime = Field(default_factory=datetime.utcnow)
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
    name: str
    description: Optional[str] = None
    rules: Optional[str] = None
    creator_id: int = Field(index=True)
    is_public: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    avatar_url: Optional[str] = None


class BookClubMember(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    club_id: int = Field(index=True)
    user_id: int = Field(index=True)
    role: str = Field(default="member")
    joined_at: datetime = Field(default_factory=datetime.utcnow)


class BookClubBook(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    club_id: int = Field(index=True)
    book_id: int = Field(index=True)
    status: str = Field(default="reading")
    added_at: datetime = Field(default_factory=datetime.utcnow)


class BookClubDiscussion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    club_id: int = Field(index=True)
    user_id: int = Field(index=True)
    title: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class BookClubComment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    discussion_id: Optional[int] = Field(default=None, index=True) 
    meeting_id: Optional[int] = Field(default=None, index=True) 
    
    user_id: int = Field(index=True)
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class BookClubMeeting(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    club_id: int = Field(index=True)
    book_id: Optional[int] = Field(default=None, index=True) 

    title: str
    date: datetime
    location: Optional[str] = Field(default=None) 
    agenda: Optional[str] = Field(default=None)  

    created_at: datetime = Field(default_factory=datetime.utcnow)
    
class InviteStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"

class BookClubInvitation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    club_id: int = Field(index=True, foreign_key="bookclub.id")
    sender_id: int = Field(index=True) 
    receiver_id: int = Field(index=True) 
    
    status: InviteStatus = Field(
        default=InviteStatus.PENDING, 
        sa_column=Column(SqlEnum(InviteStatus))
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    type: Optional[str] = Field(default="invite", description="invite | request")


class BuddyRead(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    book_id: int = Field(index=True, foreign_key="books.id")
    created_by_user_id: int = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Thêm Relationship
    members: List["BuddyReadMember"] = Relationship(back_populates="buddy_read")
    comments: List["BuddyReadComment"] = Relationship(back_populates="buddy_read")
    invitations: List["BuddyReadInvitation"] = Relationship(back_populates="buddy_read")

class BuddyReadMember(SQLModel, table=True):
    # Thêm UniqueConstraint
    __table_args__ = (UniqueConstraint("buddy_read_id", "user_id"),)
    
    id: Optional[int] = Field(default=None, primary_key=True)
    buddy_read_id: int = Field(index=True, foreign_key="buddyread.id")
    user_id: int = Field(index=True)
    joined_at: datetime = Field(default_factory=datetime.utcnow)

    # Thêm Relationship
    buddy_read: Optional["BuddyRead"] = Relationship(back_populates="members")

class BuddyReadComment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    buddy_read_id: int = Field(index=True, foreign_key="buddyread.id")
    user_id: int = Field(index=True)
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Thêm Relationship
    buddy_read: Optional["BuddyRead"] = Relationship(back_populates="comments")

class BuddyReadInvitation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    buddy_read_id: int = Field(index=True, foreign_key="buddyread.id")
    sender_id: int = Field(index=True)
    receiver_id: int = Field(index=True)
    status: InviteStatus = Field(
        default=InviteStatus.PENDING, 
        sa_column=Column(SqlEnum(InviteStatus))
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Thêm Relationship
    buddy_read: Optional["BuddyRead"] = Relationship(back_populates="invitations")

class AiSummaryCache(SQLModel, table=True):
    book_id: int = Field(primary_key=True, foreign_key="books.id")
    summary_text: str = Field(sa_column=Column(Text))
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    
class AnnualChallenge(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    year: int = Field(index=True) # Ví dụ: 2025
    goal_count: int # Mục tiêu (ví dụ: 20 cuốn)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
class BookAudio(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    book_id: int = Field(foreign_key="books.id", index=True)
    title: str 
    file_url: str 
    duration: Optional[str] = None 
    order: int = Field(default=0) 
    
class BookQuote(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    book_id: int = Field(foreign_key="books.id", index=True, nullable=False)
    user_id: int = Field(index=True, nullable=False)
    content: str = Field(sa_column=Column(Text, nullable=False))
    
    like_count: int = Field(default=0, index=True) 
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Quan hệ ngược
    likes: List["BookQuoteLike"] = Relationship(back_populates="quote")
    
class BookQuoteLike(SQLModel, table=True):
    user_id: int = Field(primary_key=True)
    quote_id: int = Field(foreign_key="bookquote.id", primary_key=True)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Quan hệ
    quote: "BookQuote" = Relationship(back_populates="likes")


class UserBookAnnotation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, nullable=False)
    book_id: int = Field(foreign_key="books.id", index=True, nullable=False)
    
    cfi_range: str = Field(nullable=False) 
    text_content: str = Field(nullable=True) 
    note_content: Optional[str] = None
    
    type: str = Field(default="highlight")
    color: str = Field(default="yellow")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)