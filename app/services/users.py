from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserAdminCreate, UserUpdate
from app.services.auth import get_user_by_email, hash_password


def list_users(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
    return db.query(User).offset(skip).limit(limit).all()


def update_user(db: Session, user: User, user_in: UserUpdate) -> User:
    if user_in.email is not None and user_in.email != user.email:
        if get_user_by_email(db, user_in.email):
            raise ValueError("Email already registered")
        user.email = user_in.email
    if user_in.full_name is not None:
        user.full_name = user_in.full_name
    if user_in.role is not None:
        user.role = user_in.role
    if user_in.is_active is not None:
        user.is_active = user_in.is_active
    if user_in.password is not None:
        user.hashed_password = hash_password(user_in.password)
    db.commit()
    db.refresh(user)
    return user


def create_user_admin(db: Session, user_in: UserAdminCreate) -> User:
    if get_user_by_email(db, user_in.email):
        raise ValueError("Email already registered")
    user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=hash_password(user_in.password),
        role=user_in.role,
        is_active=user_in.is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user: User) -> None:
    db.delete(user)
    db.commit()
