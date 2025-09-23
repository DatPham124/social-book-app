from datetime import date
from typing import Optional
from sqlmodel import SQLModel, Field


class Books(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True) #Truoc khi insert chua co id, do id la tu sinh nen de Optional va default:none
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
