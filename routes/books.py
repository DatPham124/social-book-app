import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

router = APIRouter(
    prefix="/book",
    tags=["role"],
)