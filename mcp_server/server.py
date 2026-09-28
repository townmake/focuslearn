"""
FocusLearn MCP Server — expose personal time-management APIs to AI assistants.

Env:
  FOCUSLEARN_BASE_URL   e.g. http://127.0.0.1:8001
  FOCUSLEARN_USERNAME
  FOCUSLEARN_PASSWORD

Run (stdio, for Cursor):
  python -m mcp_server.server
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any, Optional

from mcp.server.fastmcp import FastMCP

from .client import FocusLearnClientError, get_client

mcp = FastMCP(
    "focuslearn",
    instructions=(
        "FocusLearn 个人时间投入管理 MCP。"
        "写入内容前先用 list_subjects / list_chapters（或 list_subject_chapter_tree）确认项目与子任务 ID；"
        "对话要点可 create_study_record；排期用 create_calendar_task；"
        "截止提醒用 create_important_date；完成计划用 toggle_task_complete。"
    ),
)


def _ok(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, default=str)


def _err(exc: Exception) -> str:
    if isinstance(exc, FocusLearnClientError):
        return _ok({"ok": False, "error": str(exc), "status_code": exc.status_code, "body": exc.body})
    return _ok({"ok": False, "error": str(exc)})


def _parse_dt(s: str) -> datetime:
    s = (s or "").strip().replace("Z", "+00:00")
    if "T" not in s and " " in s:
        s = s.replace(" ", "T", 1)
    return datetime.fromisoformat(s)


def _duration_seconds(start: str, end: str) -> int:
    a = _parse_dt(start)
    b = _parse_dt(end)
    sec = int((b - a).total_seconds())
    if sec <= 0:
        raise ValueError("结束时间必须晚于开始时间")
    return sec


# ---------- lookup ----------

@mcp.tool()
def list_subjects(include_closed: bool = False) -> str:
    """列出项目（科目）。默认只返回开启中的项目，按热度排序。写入计划/记录前先调用以取得 subject id。"""
    try:
        client = get_client()
        params = {}
        if include_closed:
            params["include_closed"] = "1"
        data = client.get("/planner/api/subjects/", params=params)
        rows = data if isinstance(data, list) else data.get("results", data)
        slim = []
        for s in rows or []:
            slim.append(
                {
                    "id": s.get("id"),
                    "name": s.get("name"),
                    "heat": s.get("heat"),
                    "open_status": s.get("open_status"),
                    "color": s.get("color"),
                    "category_id": s.get("category") or s.get("category_id"),
                }
            )
        return _ok({"ok": True, "count": len(slim), "subjects": slim})
    except Exception as e:
        return _err(e)


@mcp.tool()
def list_chapters(subject_id: int, include_done: bool = False) -> str:
    """列出某项目下的子任务/章节。默认排除已完成章节。写入前用此工具取得 chapter id。"""
    try:
        client = get_client()
        params: dict[str, Any] = {"subject": subject_id}
        # planner API uses ?subject= ; courses uses subject_id — planner is primary
        data = client.get("/planner/api/chapters/", params=params)
        rows = data if isinstance(data, list) else data.get("results", data)
        slim = []
        for c in rows or []:
            status = c.get("progress_status") or c.get("status")
            if not include_done and status in ("done", "completed", "完成"):
                continue
            slim.append(
                {
                    "id": c.get("id"),
                    "title": c.get("title") or c.get("name"),
                    "subject_id": c.get("subject") or subject_id,
                    "progress_status": status,
                    "order": c.get("order"),
                }
            )
        return _ok({"ok": True, "subject_id": subject_id, "count": len(slim), "chapters": slim})
    except Exception as e:
        return _err(e)


@mcp.tool()
def list_subject_chapter_tree() -> str:
    """一次获取「开启项目 → 未完成子任务」树，适合快速选 subject/chapter。"""
    try:
        client = get_client()
        data = client.get("/courses/subject-chapter-options/")
        return _ok({"ok": True, "tree": data})
    except Exception as e:
        return _err(e)


# ---------- calendar tasks ----------

@mcp.tool()
def list_tasks(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    unscheduled: bool = False,
    subject_id: Optional[int] = None,
    chapter_id: Optional[int] = None,
) -> str:
    """查询周历计划。日期格式 YYYY-MM-DD。unscheduled=true 时返回待安排列表。"""
    try:
        client = get_client()
        params: dict[str, Any] = {}
        if unscheduled:
            params["unscheduled"] = "1"
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if subject_id is not None:
            params["subject"] = subject_id
        if chapter_id is not None:
            params["chapter"] = chapter_id
        data = client.get("/planner/api/tasks/", params=params)
        rows = data if isinstance(data, list) else data.get("results", data)
        slim = []
        for t in rows or []:
            slim.append(
                {
                    "id": t.get("id"),
                    "title": t.get("title"),
                    "description": t.get("description"),
                    "subject_id": t.get("subject"),
                    "subject_name": t.get("subject_name"),
                    "chapter_id": t.get("chapter"),
                    "chapter_name": t.get("chapter_name"),
                    "start": t.get("start"),
                    "end": t.get("end"),
                    "start_date": t.get("start_date"),
                    "start_time": t.get("start_time"),
                    "end_date": t.get("end_date"),
                    "end_time": t.get("end_time"),
                    "is_completed": t.get("is_completed"),
                    "status": t.get("status"),
                    "is_unscheduled": t.get("is_unscheduled"),
                    "urgency_level": t.get("urgency_level"),
                    "importance_level": t.get("importance_level"),
                }
            )
        return _ok({"ok": True, "count": len(slim), "tasks": slim})
    except Exception as e:
        return _err(e)


@mcp.tool()
def create_calendar_task(
    title: str,
    subject_id: int,
    chapter_id: int,
    start_date: Optional[str] = None,
    start_time: Optional[str] = None,
    end_date: Optional[str] = None,
    end_time: Optional[str] = None,
    description: str = "",
    is_unscheduled: bool = False,
    urgency_level: str = "low",
    importance_level: str = "low",
    repeat_type: str = "none",
) -> str:
    """
    创建周历计划或待安排任务。
    - 有明确时间：传 start_date/start_time/end_date/end_time（日期 YYYY-MM-DD，时间 HH:MM 或 HH:MM:SS）
    - 仅记下待办、稍后安排：is_unscheduled=true（可不传时间）
    title 建议用对话要点摘要；description 可放原文要点。
    """
    try:
        client = get_client()
        body: dict[str, Any] = {
            "title": title,
            "description": description or "",
            "subject": subject_id,
            "chapter": chapter_id,
            "is_unscheduled": bool(is_unscheduled),
            "urgency_level": urgency_level or "low",
            "importance_level": importance_level or "low",
            "repeat_type": "none" if is_unscheduled else (repeat_type or "none"),
        }
        if not is_unscheduled:
            if not (start_date and start_time and end_date and end_time):
                # default: today 09:00-10:00 local wall clock strings if omitted partially
                raise ValueError("排入日历时需要 start_date/start_time/end_date/end_time；或设 is_unscheduled=true")
            body.update(
                {
                    "start_date": start_date,
                    "start_time": start_time if len(start_time) > 5 else f"{start_time}:00",
                    "end_date": end_date,
                    "end_time": end_time if len(end_time) > 5 else f"{end_time}:00",
                }
            )
        data = client.post("/planner/api/tasks/", json_body=body)
        return _ok({"ok": True, "task": data})
    except Exception as e:
        return _err(e)


@mcp.tool()
def update_calendar_task(
    task_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    start_date: Optional[str] = None,
    start_time: Optional[str] = None,
    end_date: Optional[str] = None,
    end_time: Optional[str] = None,
    is_unscheduled: Optional[bool] = None,
    urgency_level: Optional[str] = None,
    importance_level: Optional[str] = None,
    update_scope: str = "this",
) -> str:
    """更新计划。重复系列可用 update_scope=this|following|all。"""
    try:
        client = get_client()
        body: dict[str, Any] = {"update_scope": update_scope or "this"}
        for key, val in [
            ("title", title),
            ("description", description),
            ("start_date", start_date),
            ("start_time", start_time),
            ("end_date", end_date),
            ("end_time", end_time),
            ("is_unscheduled", is_unscheduled),
            ("urgency_level", urgency_level),
            ("importance_level", importance_level),
        ]:
            if val is not None:
                body[key] = val
        data = client.patch(f"/planner/api/tasks/{task_id}/", json_body=body)
        return _ok({"ok": True, "task": data})
    except Exception as e:
        return _err(e)


@mcp.tool()
def toggle_task_complete(task_id: int) -> str:
    """切换计划完成状态（待办 ↔ 完成）。"""
    try:
        client = get_client()
        data = client.post(f"/planner/api/tasks/{task_id}/toggle_complete/")
        return _ok({"ok": True, "task": data})
    except Exception as e:
        return _err(e)


@mcp.tool()
def plan_execution_record(
    task_id: int,
    learning_content: str,
    start_time: str,
    end_time: str,
    mark_complete: bool = True,
    page_type: str = "other",
    chapter_id: Optional[int] = None,
    description: str = "",
) -> str:
    """
    在原计划上记录实际执行内容；mark_complete=true 时同时将计划标为完成。
    start_time/end_time 用 ISO 本地时间，如 2026-09-28T14:00:00。
    """
    try:
        client = get_client()
        body: dict[str, Any] = {
            "learning_content": learning_content,
            "description": description or "",
            "start_time": start_time,
            "end_time": end_time,
            "mark_complete": bool(mark_complete),
            "page_type": page_type or "other",
        }
        if chapter_id is not None:
            body["chapter"] = chapter_id
        data = client.post(f"/planner/api/tasks/{task_id}/plan_execution_record/", json_body=body)
        return _ok({"ok": True, "result": data})
    except Exception as e:
        return _err(e)


# ---------- study records ----------

@mcp.tool()
def create_study_record(
    learning_content: str,
    subject_id: int,
    chapter_id: int,
    start_time: str,
    end_time: Optional[str] = None,
    duration_minutes: Optional[int] = None,
    page_type: str = "thinking",
    description: str = "",
    subject_name: str = "",
    chapter_name: str = "",
) -> str:
    """
    手动插入一条学习/投入记录（日历上显示红点）。适合把对话重要内容落库。
    start_time/end_time：ISO，如 2026-09-28T15:30:00。
    若只给 start_time，可用 duration_minutes（默认 30）推算结束时间。
    page_type: research|thinking|communication|implementation|retrospective|process_step|other
    """
    try:
        client = get_client()
        start = _parse_dt(start_time)
        if end_time:
            end = _parse_dt(end_time)
        else:
            mins = duration_minutes if duration_minutes and duration_minutes > 0 else 30
            end = start + timedelta(minutes=mins)
        duration = int((end - start).total_seconds())
        if duration <= 0:
            raise ValueError("结束时间必须晚于开始时间")

        # resolve names if omitted
        subj_name = subject_name
        chap_name = chapter_name
        if not subj_name or not chap_name:
            try:
                chapters = client.get("/planner/api/chapters/", params={"subject": subject_id})
                rows = chapters if isinstance(chapters, list) else chapters.get("results", [])
                for c in rows or []:
                    if c.get("id") == chapter_id:
                        chap_name = chap_name or c.get("title") or c.get("name") or ""
                        break
                subjects = client.get("/planner/api/subjects/")
                srows = subjects if isinstance(subjects, list) else subjects.get("results", [])
                for s in srows or []:
                    if s.get("id") == subject_id:
                        subj_name = subj_name or s.get("name") or ""
                        break
            except Exception:
                pass

        body = {
            "created_date": start.date().isoformat(),
            "start_time": start.isoformat(timespec="seconds"),
            "end_time": end.isoformat(timespec="seconds"),
            "duration": duration,
            "page_type": page_type or "thinking",
            "chapter": chapter_id,
            "subject_name": subj_name or "—",
            "chapter_name": chap_name or "—",
            "learning_content": learning_content,
            "description": description or "",
        }
        data = client.post("/courses/api/study-records/", json_body=body)
        return _ok({"ok": True, "record": data})
    except Exception as e:
        return _err(e)


@mcp.tool()
def search_study_records(
    content_search: str = "",
    created_date_start: Optional[str] = None,
    created_date_end: Optional[str] = None,
    subject_id: Optional[int] = None,
    chapter_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
) -> str:
    """按内容/日期/项目搜索学习记录。"""
    try:
        client = get_client()
        params: dict[str, Any] = {"page": page, "page_size": page_size}
        if content_search:
            params["content_search"] = content_search
        if created_date_start and created_date_end:
            params["created_date_start"] = created_date_start
            params["created_date_end"] = created_date_end
        if subject_id is not None:
            params["subject"] = subject_id
        if chapter_id is not None:
            params["chapter"] = chapter_id
        data = client.get("/courses/api/study-records/list/", params=params)
        return _ok({"ok": True, "result": data})
    except Exception as e:
        return _err(e)


# ---------- important dates ----------

@mcp.tool()
def list_important_dates() -> str:
    """列出重要日期/截止提醒。"""
    try:
        client = get_client()
        data = client.get("/planner/api/important-dates/")
        return _ok({"ok": True, "result": data})
    except Exception as e:
        return _err(e)


@mcp.tool()
def create_important_date(
    name: str,
    due_at: str,
    subject_id: int,
    chapter_id: int,
    description: str = "",
) -> str:
    """
    创建重要日期（会同步生成周历任务）。
    due_at：本地 ISO，如 2026-10-01T18:00 或 2026-10-01T18:00:00。
    """
    try:
        client = get_client()
        body = {
            "name": name,
            "description": description or "",
            "due_at": due_at,
            "subject": subject_id,
            "chapter": chapter_id,
        }
        data = client.post("/planner/api/important-dates/", json_body=body)
        return _ok({"ok": True, "result": data})
    except Exception as e:
        return _err(e)


@mcp.tool()
def ping_focuslearn() -> str:
    """检查能否登录并访问 FocusLearn API。"""
    try:
        client = get_client()
        client.ensure_login()
        subjects = client.get("/planner/api/subjects/")
        rows = subjects if isinstance(subjects, list) else subjects.get("results", [])
        return _ok(
            {
                "ok": True,
                "base_url": client.base_url,
                "username": client.username,
                "subject_count": len(rows or []),
            }
        )
    except Exception as e:
        return _err(e)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
