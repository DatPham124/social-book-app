from fastapi import FastAPI
from .routes import users, admin, profiles, friend
from common_lib.database import engine_user_srevice
from sqlmodel import SQLModel, Session, select
from .model import Role

app = FastAPI()

@app.on_event("startup")
def on_startup():
    # SQLModel.metadata.drop_all(engine_user_srevice)

    SQLModel.metadata.create_all(engine_user_srevice)
    with Session(engine_user_srevice) as session:
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
app.include_router(admin.router)
app.include_router(friend.router)
