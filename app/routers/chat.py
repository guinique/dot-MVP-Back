from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.dependencies.embed import verify_embed_token
from app.models.tutor import TutorStatus
from app.schemas.chat import ChatMessageRequest, ChatMessageResponse, ChatSessionCreate, ChatSessionResponse
from app.services import tutors as tutors_service

router = APIRouter(prefix="/chat", tags=["chat"])
settings = get_settings()


@router.post("/sessions", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
def create_chat_session(
    payload: ChatSessionCreate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(verify_embed_token)],
) -> ChatSessionResponse:
    tutor = tutors_service.get_tutor(db, payload.tutor_id)
    if not tutor or tutor.status != TutorStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active tutor not found")
    session = tutors_service.get_or_create_session(db, tutor, session_key=None)
    return ChatSessionResponse(
        session_id=session.id, session_key=session.session_key, tutor_id=tutor.id
    )


@router.post("/tutors/{tutor_id}/messages", response_model=ChatMessageResponse)
def send_message(
    tutor_id: int,
    payload: ChatMessageRequest,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(verify_embed_token)],
) -> ChatMessageResponse:
    tutor = tutors_service.get_tutor(db, tutor_id)
    if not tutor or tutor.status != TutorStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active tutor not found")

    session, reply = tutors_service.chat_with_tutor(
        db, tutor, payload, history_limit=settings.chat_history_limit
    )
    return ChatMessageResponse(session_id=session.id, session_key=session.session_key, reply=reply)
