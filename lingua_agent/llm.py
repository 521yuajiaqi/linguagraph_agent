from __future__ import annotations

import os
from pathlib import Path


class LLMClient:
    """Small adapter around a chat model with a deterministic fallback."""

    def __init__(self) -> None:
        self._chat_model = None
        self._load_env_files()

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return

        try:
            from langchain_openai import ChatOpenAI

            model = os.getenv("LINGUAGRAPH_MODEL", "gpt-4o-mini")
            base_url = (
                os.getenv("OPENAI_BASE_URL")
                or os.getenv("OPENAI_API_BASE")
                or os.getenv("OPENAI_API_URL")
            )
            kwargs = {"model": model, "temperature": 0.2}
            if base_url:
                kwargs["base_url"] = base_url.rstrip("/")
            self._chat_model = ChatOpenAI(**kwargs)
        except Exception:
            self._chat_model = None

    def complete(self, system: str, user: str) -> str:
        if self._chat_model is None:
            return self._fallback(system, user)

        try:
            response = self._chat_model.invoke(
                [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ]
            )
            return str(response.content)
        except Exception as exc:
            return self._fallback(system, user, exc)

    @staticmethod
    def _fallback(system: str, user: str, exc: Exception | None = None) -> str:
        reason = f"调用大模型失败：{exc.__class__.__name__}。" if exc else "当前未检测到可用的大模型客户端。"
        return (
            f"{reason}已使用本地模板输出。"
            "请配置 OPENAI_API_KEY、OPENAI_BASE_URL 并安装 langchain-openai 后获得完整生成能力。\n\n"
            f"任务摘要：{user[:300]}"
        )

    @staticmethod
    def _load_env_files() -> None:
        try:
            from dotenv import load_dotenv

            root = Path(__file__).resolve().parents[1]
            load_dotenv(root / ".env")
            load_dotenv(root / "openai.env")
        except Exception:
            return
