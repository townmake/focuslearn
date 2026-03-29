"""
首页欢迎区名言：Quotable 随机名言 API。
文档：https://github.com/lukePeavey/quotable · 服务端 https://api.quotable.io
"""
import json
import logging
import random
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.db import IntegrityError
from django.utils import timezone

logger = logging.getLogger(__name__)

QUOTABLE_RANDOM_BASE = "https://api.quotable.io/quotes/random"


def _parse_quote_item(q):
    content = (q.get("content") or "").strip()
    author = (q.get("author") or "未知").strip()
    if not content:
        return None
    return {"content": content[:4000], "author": author[:200]}


def fetch_quotes_batch(limit=1):
    """一次请求拉取多条随机名言（limit 1–50，见 Quotable API）。"""
    n = min(50, max(1, int(limit)))
    url = f"{QUOTABLE_RANDOM_BASE}?limit={n}"
    req = Request(
        url,
        headers={"User-Agent": "FocusLearn/1.0 (Django; home quote)"},
    )
    with urlopen(req, timeout=12) as resp:
        raw = resp.read().decode("utf-8")
    data = json.loads(raw)
    if not isinstance(data, list):
        data = [data]
    out = []
    for item in data:
        parsed = _parse_quote_item(item)
        if parsed:
            out.append(parsed)
    if not out:
        raise ValueError("no valid quotes in response")
    return out


def fetch_one_quote():
    """单条随机名言；失败时抛出异常。"""
    batch = fetch_quotes_batch(1)
    return batch[0]


def ensure_today_quotable_quotes(slots=None):
    """
    保证「今天」指定时段（或全部三个时段）在库中各有一条记录；缺则向 API 拉取并写入。
    slots: None 表示 morning/noon/evening 全部；否则为 Slot 取值列表。
    """
    from .models import DailyQuotableQuote

    today = timezone.localdate()
    if slots is None:
        slot_values = [c[0] for c in DailyQuotableQuote.Slot.choices]
    else:
        slot_values = list(slots)

    to_fill = [
        s
        for s in slot_values
        if not DailyQuotableQuote.objects.filter(date=today, slot=s).exists()
    ]
    if not to_fill:
        return
    try:
        batch = fetch_quotes_batch(len(to_fill))
    except (URLError, HTTPError, TimeoutError, OSError, ValueError, json.JSONDecodeError) as e:
        logger.warning("Quotable batch fetch failed: %s", e)
        batch = []
    for i, slot in enumerate(to_fill):
        quote = batch[i] if i < len(batch) else None
        if quote is None:
            try:
                quote = fetch_one_quote()
            except (URLError, HTTPError, TimeoutError, OSError, ValueError, json.JSONDecodeError) as e:
                logger.warning("Quotable single fetch failed (slot=%s): %s", slot, e)
                continue
        try:
            DailyQuotableQuote.objects.create(
                date=today,
                slot=slot,
                content=quote["content"],
                author=quote["author"],
            )
        except IntegrityError:
            pass


def pick_random_welcome_quote():
    """从今日已存的名言中随机取一条展示；无则返回 None。"""
    from .models import DailyQuotableQuote

    today = timezone.localdate()
    rows = list(
        DailyQuotableQuote.objects.filter(date=today).values("content", "author")
    )
    if not rows:
        return None
    return random.choice(rows)


def refresh_slot(today, slot, *, force=False):
    """
    为指定日期+时段拉取并写入。force=True 时先删再建（供定时任务「更新备用」）。
    """
    from .models import DailyQuotableQuote

    if force:
        DailyQuotableQuote.objects.filter(date=today, slot=slot).delete()
    if DailyQuotableQuote.objects.filter(date=today, slot=slot).exists():
        return False
    try:
        quote = fetch_one_quote()
    except (URLError, HTTPError, TimeoutError, OSError, ValueError, json.JSONDecodeError) as e:
        logger.warning("Quotable refresh_slot failed: %s", e)
        return False
    try:
        DailyQuotableQuote.objects.create(
            date=today,
            slot=slot,
            content=quote["content"],
            author=quote["author"],
        )
    except IntegrityError:
        return False
    return True
