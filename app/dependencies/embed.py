from typing import Annotated

from fastapi import Header, HTTPException, status

from app.config import get_settings

settings = get_settings()


def verify_embed_token(
    x_embed_token: Annotated[str | None, Header()] = None,
) -> None:
    if not settings.embed_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Embed authentication is not configured",
        )
    if x_embed_token != settings.embed_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid embed token",
        )
