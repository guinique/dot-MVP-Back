import logging
import uuid

from sqlalchemy.orm import Session

from app.models.tutor import ChatMessage, ChatSession, MessageRole, Tutor, TutorStatus
from app.schemas.chat import ChatMessageRequest
from app.schemas.tutor import TutorCreate, TutorUpdate
from app.services.agent import generate_tutor_reply

logger = logging.getLogger(__name__)


def list_tutors(db: Session, skip: int = 0, limit: int = 100) -> list[Tutor]:
    return db.query(Tutor).offset(skip).limit(limit).all()


def get_tutor(db: Session, tutor_id: int) -> Tutor | None:
    return db.query(Tutor).filter(Tutor.id == tutor_id).first()


def create_tutor(db: Session, tutor_in: TutorCreate) -> Tutor:
    tutor = Tutor(
        title=tutor_in.title,
        description=tutor_in.description,
        system_instructions=tutor_in.system_instructions,
        status=tutor_in.status,
        source_urls=[str(url) for url in tutor_in.source_urls],
    )
    db.add(tutor)
    db.commit()
    db.refresh(tutor)
    return tutor


def update_tutor(db: Session, tutor: Tutor, tutor_in: TutorUpdate) -> Tutor:
    if tutor_in.title is not None:
        tutor.title = tutor_in.title
    if tutor_in.description is not None:
        tutor.description = tutor_in.description
    if tutor_in.system_instructions is not None:
        tutor.system_instructions = tutor_in.system_instructions
    if tutor_in.status is not None:
        tutor.status = tutor_in.status
    if tutor_in.source_urls is not None:
        tutor.source_urls = [str(url) for url in tutor_in.source_urls]
    db.commit()
    db.refresh(tutor)
    return tutor


def deactivate_tutor(db: Session, tutor: Tutor) -> Tutor:
    tutor.status = TutorStatus.INACTIVE
    db.commit()
    db.refresh(tutor)
    return tutor


def delete_tutor(db: Session, tutor: Tutor) -> None:
    db.delete(tutor)
    db.commit()


def get_or_create_session(db: Session, tutor: Tutor, session_key: str | None) -> ChatSession:
    if session_key:
        session = (
            db.query(ChatSession)
            .filter(ChatSession.session_key == session_key, ChatSession.tutor_id == tutor.id)
            .first()
        )
        if session:
            return session

    session = ChatSession(tutor_id=tutor.id, session_key=session_key or uuid.uuid4().hex)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_recent_messages(db: Session, session_id: int, limit: int) -> list[ChatMessage]:
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
        .limit(limit)
        .all()[::-1]
    )


def get_session_history(
    db: Session,
    tutor: Tutor,
    session_key: str,
    limit: int,
) -> tuple[ChatSession, list[ChatMessage]] | None:
    session = (
        db.query(ChatSession)
        .filter(ChatSession.session_key == session_key, ChatSession.tutor_id == tutor.id)
        .first()
    )
    if not session:
        return None
    return session, get_recent_messages(db, session.id, limit)


def chat_with_tutor(
    db: Session,
    tutor: Tutor,
    payload: ChatMessageRequest,
    history_limit: int,
) -> tuple[ChatSession, str]:
    session = get_or_create_session(db, tutor, payload.session_key)
    history = get_recent_messages(db, session.id, history_limit)

    user_message = ChatMessage(
        session_id=session.id, role=MessageRole.USER, content=payload.message
    )
    db.add(user_message)
    db.commit()

    reply = generate_tutor_reply(
        tutor=tutor,
        history=history,
        user_message=payload.message,
        session_key=session.session_key,
    )

    assistant_message = ChatMessage(
        session_id=session.id, role=MessageRole.ASSISTANT, content=reply
    )
    db.add(assistant_message)
    db.commit()

    return session, reply
