"""AiEditor 图片上传：返回格式需符合 AiEditor 约定 errorCode + data.src。"""
import os
import uuid

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST

_ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
_ALLOWED_CT = {"image/jpeg", "image/png", "image/gif", "image/webp"}


@require_POST
def aieditor_image_upload(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"errorCode": 1, "message": "请先登录"},
            status=401,
        )

    f = request.FILES.get("image")
    if not f:
        return JsonResponse({"errorCode": 1, "message": "未收到图片文件"})

    ext = os.path.splitext(f.name or "")[1].lower()
    if ext not in _ALLOWED_EXT:
        return JsonResponse({"errorCode": 1, "message": "仅支持 jpg、png、gif、webp"})

    if f.content_type and f.content_type not in _ALLOWED_CT:
        return JsonResponse({"errorCode": 1, "message": "不支持的图片类型"})

    max_bytes = getattr(settings, "FILE_UPLOAD_MAX_MEMORY_SIZE", 10 * 1024 * 1024)
    if f.size > max_bytes:
        return JsonResponse({"errorCode": 1, "message": "图片过大"})

    subdir = "editor_images"
    name = f"{uuid.uuid4().hex}{ext}"
    rel_path = f"{subdir}/{name}".replace("\\", "/")
    abs_dir = os.path.join(settings.MEDIA_ROOT, subdir)
    os.makedirs(abs_dir, exist_ok=True)
    abs_path = os.path.join(settings.MEDIA_ROOT, rel_path)

    with open(abs_path, "wb") as dest:
        for chunk in f.chunks():
            dest.write(chunk)

    media_url = settings.MEDIA_URL
    if not media_url.endswith("/"):
        media_url = media_url + "/"
    src = request.build_absolute_uri(media_url + rel_path)

    return JsonResponse(
        {
            "errorCode": 0,
            "data": {
                "src": src,
                "alt": (f.name or "")[:200],
            },
        }
    )
