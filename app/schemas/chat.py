from pydantic import BaseModel, Field


class ChatSessionCreate(BaseModel):
    tutor_id: int


class ChatSessionResponse(BaseModel):
    session_id: int
    session_key: str
    tutor_id: int


class ChatMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_key: str | None = None


class ChatMessageResponse(BaseModel):
    session_id: int
    session_key: str
    reply: str
    role: str = "assistant"
