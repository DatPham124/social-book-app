# database.py
from sqlmodel import create_engine, Session
from .config import MYSQL_URL

engine = create_engine(MYSQL_URL, echo=True)

def get_session():
    with Session(engine) as session:
        yield session
