import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from common_lib.auth import require_admin
from common_lib.database import get_session_user_service
from ..model import User_role, Role

router = APIRouter(
    prefix="/users/admin",
    tags=["role"],
    dependencies=[Depends(require_admin)]
)

@router.post("/assign/role", response_model=User_role)
def assign_role(user_role_data: User_role, session: Session = Depends(get_session_user_service)):
    user_uuid = uuid.UUID(user_role_data.user_id)
    role_uuid = uuid.UUID(user_role_data.role_id)

    user_role_data.user_id = user_uuid
    user_role_data.role_id = role_uuid

    
    statement = select(User_role).where(
        User_role.user_id == user_role_data.user_id,
        User_role.role_id == user_role_data.role_id
    )
    existing = session.exec(statement).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already has this role assigned")

    session.add(user_role_data)
    session.commit()
    session.refresh(user_role_data)
    return user_role_data


@router.delete("/assign/delete/{assign_id}")
def delete_user_role(assign_id: int, session: Session = Depends(get_session_user_service)):
    user_role = session.get(User_role, assign_id)
    if not user_role:
        raise HTTPException(status_code=404, detail="User role not found")

    session.delete(user_role)
    session.commit()
    return {"detail": f"User role with ID {assign_id} deleted successfully"}


@router.post("/add/role", response_model=Role)
def add_role(role_data: Role, session: Session = Depends(get_session_user_service)):
    statement = select(Role).where(Role.role_name == role_data.role_name)
    existing = session.exec(statement).first()
    if existing:
        raise HTTPException(status_code=400, detail="Role with this name already exists")

    session.add(role_data)
    session.commit()
    session.refresh(role_data)
    return role_data


@router.delete("/delete/role{role_id}")
def delete_role(role_id, session: Session = Depends(get_session_user_service)):
    role_id_uuid = uuid.UUID(role_id)

    role = session.get(Role, role_id_uuid)

    Role.role_id = role_id_uuid
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    session.delete(role)
    session.commit()
    return {"detail": f"Role with ID {role_id} deleted successfully"}
