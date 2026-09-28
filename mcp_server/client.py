"""
FocusLearn HTTP client for MCP tools.

Uses Django session login + CSRF so both DRF endpoints and
@login_required JSON APIs (e.g. important dates) work.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urljoin

import requests


def _load_dotenv(path: Path) -> None:
    """Load simple KEY=VALUE lines into os.environ if not already set."""
    if not path.is_file():
        return
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = val


# Prefer project .env when running as Cursor MCP (cwd = repo root)
_load_dotenv(Path(__file__).resolve().parent.parent / ".env")


class FocusLearnClientError(RuntimeError):
    def __init__(self, message: str, status_code: int | None = None, body: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class FocusLearnClient:
    def __init__(
        self,
        base_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.base_url = (base_url or os.environ.get("FOCUSLEARN_BASE_URL") or "http://127.0.0.1:8001").rstrip("/") + "/"
        self.username = username or os.environ.get("FOCUSLEARN_USERNAME") or ""
        self.password = password or os.environ.get("FOCUSLEARN_PASSWORD") or ""
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json", "User-Agent": "focuslearn-mcp/1.0"})
        self._logged_in = False

    def ensure_login(self) -> None:
        if self._logged_in:
            return
        if not self.username or not self.password:
            raise FocusLearnClientError(
                "缺少登录凭据：请设置环境变量 FOCUSLEARN_USERNAME / FOCUSLEARN_PASSWORD"
            )

        login_url = urljoin(self.base_url, "login/")
        r = self.session.get(login_url, timeout=self.timeout)
        r.raise_for_status()
        csrf = self.session.cookies.get("csrftoken")
        if not csrf:
            m = re.search(r'name=["\']csrfmiddlewaretoken["\']\s+value=["\']([^"\']+)', r.text)
            csrf = m.group(1) if m else None
        if not csrf:
            raise FocusLearnClientError("无法从登录页取得 CSRF token")

        payload = {
            "username": self.username,
            "password": self.password,
            "csrfmiddlewaretoken": csrf,
        }
        headers = {
            "Referer": login_url,
            "X-CSRFToken": csrf,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        r2 = self.session.post(
            login_url,
            data=payload,
            headers=headers,
            timeout=self.timeout,
            allow_redirects=False,
        )
        # Django login typically 302 on success
        if r2.status_code not in (200, 302, 303):
            raise FocusLearnClientError(
                f"登录失败 HTTP {r2.status_code}",
                status_code=r2.status_code,
                body=r2.text[:500],
            )
        if "sessionid" not in self.session.cookies:
            # Some setups keep user on login page with 200
            if "csrfmiddlewaretoken" in (r2.text or "") and "password" in (r2.text or "").lower():
                raise FocusLearnClientError("登录失败：用户名或密码错误")
        self._logged_in = True

    def _csrf_headers(self) -> dict[str, str]:
        csrf = self.session.cookies.get("csrftoken") or ""
        h = {"X-CSRFToken": csrf, "Referer": self.base_url}
        if csrf:
            h["X-CSRFToken"] = csrf
        return h

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[dict] = None,
        json_body: Any = None,
        data: Any = None,
        expect_json: bool = True,
    ) -> Any:
        self.ensure_login()
        url = urljoin(self.base_url, path.lstrip("/"))
        headers = self._csrf_headers()
        if json_body is not None:
            headers["Content-Type"] = "application/json"
        r = self.session.request(
            method.upper(),
            url,
            params=params,
            json=json_body,
            data=data,
            headers=headers,
            timeout=self.timeout,
        )
        if r.status_code >= 400:
            body: Any
            try:
                body = r.json()
            except Exception:
                body = r.text[:800]
            raise FocusLearnClientError(
                f"{method.upper()} {path} 失败 HTTP {r.status_code}: {body}",
                status_code=r.status_code,
                body=body,
            )
        if r.status_code == 204 or not r.content:
            return None
        if not expect_json:
            return r.text
        try:
            return r.json()
        except Exception:
            return r.text

    def get(self, path: str, **kwargs: Any) -> Any:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> Any:
        return self.request("POST", path, **kwargs)

    def patch(self, path: str, **kwargs: Any) -> Any:
        return self.request("PATCH", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> Any:
        return self.request("DELETE", path, **kwargs)


_client: FocusLearnClient | None = None


def get_client() -> FocusLearnClient:
    global _client
    if _client is None:
        _client = FocusLearnClient()
    return _client
