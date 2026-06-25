from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_admin
from app.models.user import User
from app.schemas.tutor import TutorCreate, TutorResponse, TutorUpdate
from app.services import tutors as tutors_service

router = APIRouter(prefix="/tutors", tags=["tutors"])


@router.get("", response_model=list[TutorResponse])
def list_tutors(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[TutorResponse]:
    return [TutorResponse.from_orm_tutor(t) for t in tutors_service.list_tutors(db, skip, limit)]


@router.post("", response_model=TutorResponse, status_code=status.HTTP_201_CREATED)
def create_tutor(
    tutor_in: TutorCreate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> TutorResponse:
    tutor = tutors_service.create_tutor(db, tutor_in)
    return TutorResponse.from_orm_tutor(tutor)


@router.get("/{tutor_id}", response_model=TutorResponse)
def get_tutor(
    tutor_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> TutorResponse:
    tutor = tutors_service.get_tutor(db, tutor_id)
    if not tutor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tutor not found")
    return TutorResponse.from_orm_tutor(tutor)


@router.patch("/{tutor_id}", response_model=TutorResponse)
def update_tutor(
    tutor_id: int,
    tutor_in: TutorUpdate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> TutorResponse:
    tutor = tutors_service.get_tutor(db, tutor_id)
    if not tutor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tutor not found")
    updated = tutors_service.update_tutor(db, tutor, tutor_in)
    return TutorResponse.from_orm_tutor(updated)


@router.post("/{tutor_id}/deactivate", response_model=TutorResponse)
def deactivate_tutor(
    tutor_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> TutorResponse:
    tutor = tutors_service.get_tutor(db, tutor_id)
    if not tutor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tutor not found")
    deactivated = tutors_service.deactivate_tutor(db, tutor)
    return TutorResponse.from_orm_tutor(deactivated)


@router.delete("/{tutor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tutor(
    tutor_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> None:
    tutor = tutors_service.get_tutor(db, tutor_id)
    if not tutor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tutor not found")
    tutors_service.delete_tutor(db, tutor)
