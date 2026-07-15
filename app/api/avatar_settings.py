from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, UploadFile

from app.core.auth import require_roles
from app.schemas.avatar_settings import AvatarSettingsResponse, AvatarSettingsUpdate
from app.core.config import settings
from app.core.errors import AppError
from app.services.avatar_settings import get_avatar_settings, save_avatar_image, save_avatar_settings

router = APIRouter(prefix="/api/avatar-settings")


@router.get("", response_model=AvatarSettingsResponse)
async def read_avatar_settings():
    return AvatarSettingsResponse(**get_avatar_settings())


@router.put("", response_model=AvatarSettingsResponse, dependencies=[Depends(require_roles("admin"))])
async def update_avatar_settings(req: AvatarSettingsUpdate):
    return AvatarSettingsResponse(**save_avatar_settings(req.model_dump()))


@router.post(
    "/image",
    response_model=AvatarSettingsResponse,
    dependencies=[Depends(require_roles("admin"))],
)
async def upload_avatar_image(file: UploadFile = File(...)):
    suffix = Path(file.filename or "").suffix.lower()
    allowed = {
        ".png": {"image/png"},
        ".jpg": {"image/jpeg"},
        ".jpeg": {"image/jpeg"},
        ".webp": {"image/webp"},
    }
    if suffix not in allowed or file.content_type not in allowed[suffix]:
        raise AppError(415, "UNSUPPORTED_AVATAR_IMAGE", "请选择 PNG、JPG 或 WebP 图片")
    directory = Path("uploads") / "avatar"
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f"avatar_{uuid4().hex}{suffix}"
    temporary = target.with_suffix(target.suffix + ".part")
    total = 0
    header = b""
    try:
        with temporary.open("wb") as output:
            while chunk := await file.read(1024 * 1024):
                if not header:
                    header = chunk[:16]
                total += len(chunk)
                if total > settings.max_vision_bytes:
                    raise AppError(413, "AVATAR_IMAGE_TOO_LARGE", "讲解形象图片过大")
                output.write(chunk)
        valid_header = (
            (suffix == ".png" and header.startswith(b"\x89PNG\r\n\x1a\n"))
            or (suffix in {".jpg", ".jpeg"} and header.startswith(b"\xff\xd8\xff"))
            or (suffix == ".webp" and header.startswith(b"RIFF") and header[8:12] == b"WEBP")
        )
        if not valid_header:
            raise AppError(415, "INVALID_AVATAR_IMAGE", "图片内容与文件格式不一致")
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
        await file.close()
    return AvatarSettingsResponse(**save_avatar_image(f"/uploads/avatar/{target.name}"))
