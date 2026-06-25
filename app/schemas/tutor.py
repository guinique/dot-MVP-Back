from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.models.tutor import TutorStatus


class TutorBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=500)
    system_instructions: str = Field(min_length=1)
    source_urls: list[HttpUrl | str] = Field(default_factory=list)


class TutorCreate(TutorBase):
    status: TutorStatus = TutorStatus.ACTIVE


class TutorUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=500)
    system_instructions: str | None = Field(default=None, min_length=1)
    status: TutorStatus | None = None
    source_urls: list[HttpUrl | str] | None = None


class TutorResponse(TutorBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: TutorStatus
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_tutor(cls, tutor) -> "TutorResponse":
        return cls(
            id=tutor.id,
            title=tutor.title,
            description=tutor.description,
            system_instructions=tutor.system_instructions,
            source_urls=tutor.source_urls or [],
            status=tutor.status,
            created_at=tutor.created_at,
            updated_at=tutor.updated_at,
        )
