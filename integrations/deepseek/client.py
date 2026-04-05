"""
DeepSeek OpenAI 兼容接口封装。
文档: https://api-docs.deepseek.com/zh-cn/
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Any, List, Optional

import requests

logger = logging.getLogger(__name__)


class DeepSeekError(Exception):
    """调用 DeepSeek API 失败。"""


@dataclass
class DeepSeekClient:
    api_key: str
    base_url: str = "https://api.deepseek.com"
    model: str = "deepseek-chat"
    timeout: int = 120

    def __post_init__(self):
        self.base_url = (self.base_url or "https://api.deepseek.com").rstrip("/")

    def chat_completion(
        self,
        messages: List[dict],
        *,
        temperature: float = 0.3,
        response_format_json: bool = True,
    ) -> str:
        """
        返回助手消息纯文本 content（若要求 JSON，则为模型输出的字符串，需自行解析）。
        """
        if not (self.api_key or "").strip():
            raise DeepSeekError("未配置 DeepSeek API Key，请在管理后台「DeepSeek API 配置」中填写。")

        url = f"{self.base_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key.strip()}",
            "Content-Type": "application/json",
        }
        body: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if response_format_json:
            body["response_format"] = {"type": "json_object"}

        try:
            resp = requests.post(url, headers=headers, json=body, timeout=self.timeout)
        except requests.RequestException as e:
            logger.exception("DeepSeek 请求异常")
            raise DeepSeekError(f"网络错误: {e}") from e

        if resp.status_code >= 400:
            try:
                err = resp.json()
                msg = err.get("error", {}).get("message") or err.get("message") or resp.text
            except Exception:
                msg = resp.text[:500]
            raise DeepSeekError(f"DeepSeek API {resp.status_code}: {msg}")

        try:
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, ValueError) as e:
            logger.warning("DeepSeek 响应解析失败: %s", resp.text[:800])
            raise DeepSeekError("DeepSeek 返回格式异常") from e


def parse_json_from_model_text(content: str) -> dict:
    """
    解析模型输出中的 JSON（支持外层 ```json 代码块）。
    """
    t = (content or "").strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", t)
    if m:
        t = m.group(1).strip()
    return json.loads(t)
