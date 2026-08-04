"""
项目列表统一搜索：项目、任务（章节）、任务下文章（知识点）。
"""
from __future__ import annotations

import re

from django.db.models import Q
from django.urls import reverse
from django.utils.html import strip_tags

from .models import Chapter, KnowledgePoint, Subject

_MAX_PER_TYPE = 30
_SNIPPET_LEN = 140


def _plain(text: str) -> str:
    return re.sub(r"\s+", " ", strip_tags(text or "").replace("\xa0", " ")).strip()


def _snippet(text: str, query: str, max_len: int = _SNIPPET_LEN) -> str:
    plain = _plain(text)
    if not plain:
        return ""
    q = (query or "").strip()
    lower = plain.lower()
    idx = lower.find(q.lower()) if q else -1
    if idx < 0:
        return plain[:max_len] + ("…" if len(plain) > max_len else "")
    start = max(0, idx - max_len // 3)
    end = min(len(plain), start + max_len)
    out = plain[start:end]
    if start > 0:
        out = "…" + out
    if end < len(plain):
        out = out + "…"
    return out


def _tokens(query: str) -> list[str]:
    """空格分词；多词时各词都要命中（同一条记录内 OR 字段、AND 词）。"""
    parts = [p for p in re.split(r"\s+", (query or "").strip()) if p]
    return parts[:8]


def _q_all_tokens(field_names: list[str], tokens: list[str]) -> Q:
    combined = Q()
    for token in tokens:
        field_or = Q()
        for name in field_names:
            field_or |= Q(**{f"{name}__icontains": token})
        combined &= field_or
    return combined


def search_subjects_tasks_articles(query: str) -> dict:
    """
    返回:
      {
        'q': str,
        'subjects': [...],
        'chapters': [...],
        'articles': [...],
        'total': int,
      }
    """
    tokens = _tokens(query)
    empty = {
        "q": (query or "").strip(),
        "subjects": [],
        "chapters": [],
        "articles": [],
        "total": 0,
    }
    # 过短关键词对正文 LIKE 代价高且易误命中 HTML 属性
    tokens = [t for t in tokens if len(t) >= 2]
    if not tokens:
        return empty

    phrase = " ".join(tokens)

    subjects_qs = (
        Subject.objects.filter(_q_all_tokens(["name", "description"], tokens))
        .select_related("category")
        .order_by("-heat", "order", "name")[:_MAX_PER_TYPE]
    )
    subjects = [
        {
            "id": s.id,
            "name": s.name,
            "description_snippet": _snippet(s.description, phrase),
            "open_status": s.open_status,
            "is_closed": s.open_status == Subject.OpenStatus.CLOSED,
            "category_name": s.category.name if s.category_id else "",
            "url": reverse("courses:subject_detail", kwargs={"pk": s.id}),
        }
        for s in subjects_qs
    ]

    chapters_qs = (
        Chapter.objects.filter(_q_all_tokens(["title", "description"], tokens))
        .select_related("subject")
        .order_by("subject__order", "order", "title")[:_MAX_PER_TYPE]
    )
    chapters = [
        {
            "id": c.id,
            "title": c.title,
            "description_snippet": _snippet(c.description, phrase),
            "subject_id": c.subject_id,
            "subject_name": c.subject.name if c.subject_id else "",
            "subject_closed": (
                c.subject.open_status == Subject.OpenStatus.CLOSED
                if c.subject_id
                else False
            ),
            "progress_status": c.progress_status,
            "url": reverse("courses:chapter_detail_page", kwargs={"pk": c.id}),
        }
        for c in chapters_qs
    ]

    # 文章：标题/描述走数据库；正文在近期记录上做纯文本匹配（避免 HTML 误命中与全文 LIKE 过慢）
    title_desc_q = _q_all_tokens(["title", "description"], tokens)
    articles_by_id = {}

    for kp in (
        KnowledgePoint.objects.filter(title_desc_q)
        .filter(chapter__isnull=False)
        .select_related("chapter", "chapter__subject")
        .order_by("-modified")[:_MAX_PER_TYPE]
    ):
        articles_by_id[kp.id] = kp

    if len(articles_by_id) < _MAX_PER_TYPE:
        recent_qs = (
            KnowledgePoint.objects.filter(chapter__isnull=False)
            .exclude(id__in=list(articles_by_id.keys()) or [0])
            .select_related("chapter", "chapter__subject")
            .order_by("-modified")[:200]
        )
        for kp in recent_qs:
            content_plain = _plain(kp.content).lower()
            if content_plain and all(t.lower() in content_plain for t in tokens):
                articles_by_id[kp.id] = kp
            if len(articles_by_id) >= _MAX_PER_TYPE:
                break

    articles = []
    for kp in articles_by_id.values():
        title_l = (kp.title or "").lower()
        desc_plain = _plain(kp.description).lower()
        content_plain = _plain(kp.content).lower()
        if not all(
            (t.lower() in title_l)
            or (t.lower() in desc_plain)
            or (t.lower() in content_plain)
            for t in tokens
        ):
            continue
        ch = kp.chapter
        subj = ch.subject if ch else None
        if all(t.lower() in title_l for t in tokens):
            hit_body = kp.description or kp.content or ""
        elif any(t.lower() in desc_plain for t in tokens):
            hit_body = kp.description or kp.content or ""
        else:
            hit_body = kp.content or kp.description or ""
        articles.append(
            {
                "id": kp.id,
                "title": kp.title,
                "snippet": _snippet(hit_body, phrase),
                "chapter_id": ch.id if ch else None,
                "chapter_title": ch.title if ch else "",
                "subject_id": subj.id if subj else None,
                "subject_name": subj.name if subj else "",
                "subject_closed": (
                    subj.open_status == Subject.OpenStatus.CLOSED if subj else False
                ),
                "url": (
                    reverse("courses:chapter_detail_page", kwargs={"pk": ch.id})
                    + f"?kp={kp.id}"
                    if ch
                    else reverse("courses:knowledgepoint_detail", kwargs={"pk": kp.id})
                ),
            }
        )
        if len(articles) >= _MAX_PER_TYPE:
            break

    return {
        "q": phrase,
        "subjects": subjects,
        "chapters": chapters,
        "articles": articles,
        "total": len(subjects) + len(chapters) + len(articles),
    }
