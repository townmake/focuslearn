"""
知识点文章导出：提供打印友好页面，便于「另存为 PDF」。
"""
from __future__ import annotations

import re
from html import unescape

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.utils.html import strip_tags
from django.utils.text import slugify

from .models import KnowledgePoint

_SRC_RE = re.compile(
    r"""(?P<prefix>\bsrc\s*=\s*)(?P<quote>['"])(?P<url>[^'"]+)(?P=quote)""",
    re.IGNORECASE,
)
_HREF_RE = re.compile(
    r"""(?P<prefix>\bhref\s*=\s*)(?P<quote>['"])(?P<url>[^'"]+)(?P=quote)""",
    re.IGNORECASE,
)


def _absolutize_url(url: str, request) -> str:
    u = (url or "").strip()
    if not u or u.startswith(("data:", "blob:", "#", "mailto:", "javascript:")):
        return u
    if u.startswith(("http://", "https://", "//")):
        return u
    return request.build_absolute_uri(u)


def absolutize_html_urls(html: str, request) -> str:
    """将正文里的相对 src/href 转为绝对地址，便于打印与另存 PDF。"""

    def _src(m: re.Match) -> str:
        return f'{m.group("prefix")}{m.group("quote")}{_absolutize_url(m.group("url"), request)}{m.group("quote")}'

    def _href(m: re.Match) -> str:
        return f'{m.group("prefix")}{m.group("quote")}{_absolutize_url(m.group("url"), request)}{m.group("quote")}'

    out = _SRC_RE.sub(_src, html or "")
    return _HREF_RE.sub(_href, out)


def _safe_filename(title: str, pk: int) -> str:
    plain = strip_tags(unescape(title or "")).strip() or f"article-{pk}"
    # slugify 对中文会变空，保留可读文件名提示
    slug = slugify(plain, allow_unicode=True) or f"article-{pk}"
    return slug[:80]


@login_required
def knowledge_point_export(request, pk):
    """文章详情导出页：浏览器打印对话框中选择「另存为 PDF」。"""
    kp = get_object_or_404(
        KnowledgePoint.objects.select_related("chapter", "chapter__subject"),
        pk=pk,
    )
    chapter = kp.chapter
    subject = chapter.subject if chapter else None
    content_html = absolutize_html_urls(kp.content or "", request)
    autoprint = (request.GET.get("autoprint") or "").strip() in ("1", "true", "yes")

    return render(
        request,
        "courses/knowledge_point_export.html",
        {
            "kp": kp,
            "chapter": chapter,
            "subject": subject,
            "content_html": content_html,
            "autoprint": autoprint,
            "export_filename": _safe_filename(kp.title, kp.pk),
        },
    )
