from fastapi import Header, HTTPException

from app.core.config import get_settings


async def require_admin_api_key(x_api_key: str | None = Header(default=None)) -> None:
    settings = get_settings()
    if not x_api_key or x_api_key != settings.admin_api_key:
        raise HTTPException(status_code=401, detail="unauthorized")
