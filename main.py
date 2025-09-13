from fastapi import FastAPI
from .routes import users, user_role, profiles
from .database import engine
from sqlmodel import SQLModel, Session, select
from .model import Role, User_role

app = FastAPI()

@app.on_event("startup")
def on_startup():

    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        existing_roles = session.exec(select(Role)).all()
        if not existing_roles:
            roles = [
                Role(role_name="admin"),
                Role(role_name="user"),
                Role(role_name="moderator"),
            ]
            session.add_all(roles)
            session.commit()


app.include_router(users.router)
app.include_router(profiles.router)
app.include_router(user_role.router)
