from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class UserAdminCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = None
    role: UserRole = UserRole.USER
    is_active: bool = True


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)
    full_name: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None
