import asyncio
import json
import urllib.error
import urllib.request
from typing import Any

from app.config import settings


class OpenAIAssistantError(Exception):
    """Base error for OpenAI integration."""


class OpenAIAssistantConfigError(OpenAIAssistantError):
    """Raised when required env vars are missing."""


class OpenAIAssistantEmptyResponseError(OpenAIAssistantError):
    """Raised when OpenAI returns no usable text."""


class OpenAIAssistantTimeoutError(OpenAIAssistantError):
    """Raised when the request times out."""


class OpenAIAssistantService:
    API_BASE_URL = "https://api.openai.com/v1"
    MAX_HISTORY = 20

    def __init__(self) -> None:
        self.api_key = settings.OPENAI_API_KEY
        self.prompt_id = settings.OPENAI_PROMPT_ID
        self.timeout = settings.OPENAI_API_TIMEOUT_SECONDS

    def _ensure_configured(self) -> None:
        if not self.api_key or not self.prompt_id:
            raise OpenAIAssistantConfigError(
                "OpenAI не настроен. Задайте OPENAI_API_KEY и OPENAI_PROMPT_ID на backend."
            )

    async def complete(
        self,
        history: list[dict],
        new_user_content: str,
        tool_choice: str | None = None,
    ) -> str:
        """Call OpenAI Responses API using the stored Chat Prompt.

        Model, system prompt, vector store, and other settings are taken
        from the stored prompt — we do NOT override the model here so the
        prompt's own configuration is used as-is.

        Pass tool_choice="required" to force File Search on the first call;
        leave None for follow-up messages so the model decides automatically.
        """
        self._ensure_configured()

        input_messages: list[dict[str, str]] = []
        for msg in history[-self.MAX_HISTORY:]:
            if not msg.get("is_error") and msg.get("role") in ("user", "assistant"):
                input_messages.append({"role": msg["role"], "content": msg["content"]})
        input_messages.append({"role": "user", "content": new_user_content})

        response = await asyncio.to_thread(self._call_responses, input_messages, tool_choice)
        return self._extract_text(response)

    def _call_responses(
        self,
        input_messages: list[dict[str, str]],
        tool_choice: str | None = None,
    ) -> dict[str, Any]:
        # Model is intentionally omitted — the stored prompt defines the model,
        # so we avoid any mismatch with model-specific parameters like reasoning_effort.
        body_dict: dict[str, Any] = {
            "prompt": {"id": self.prompt_id},
            "input": input_messages,
        }
        if tool_choice is not None:
            body_dict["tool_choice"] = tool_choice

        body = json.dumps(body_dict, ensure_ascii=False).encode("utf-8")

        request = urllib.request.Request(
            f"{self.API_BASE_URL}/responses",
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            error_msg = self._format_http_error(exc)
            print(f"[OpenAI HTTP ERROR {exc.code}] {error_msg}")
            raise OpenAIAssistantError(error_msg) from exc
        except urllib.error.URLError as exc:
            print(f"[OpenAI URL ERROR] {exc.reason}")
            raise OpenAIAssistantError(f"OpenAI API недоступен: {exc.reason}") from exc
        except TimeoutError as exc:
            print("[OpenAI TIMEOUT]")
            raise OpenAIAssistantTimeoutError("OpenAI API не ответил вовремя.") from exc
        except json.JSONDecodeError as exc:
            print(f"[OpenAI JSON ERROR] {exc}")
            raise OpenAIAssistantEmptyResponseError("OpenAI вернул невалидный JSON.") from exc

    def _extract_text(self, response: dict[str, Any]) -> str:
        for item in response.get("output", []):
            if item.get("type") != "message":
                continue
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    text = content.get("text", "").strip()
                    if text:
                        return text
        raise OpenAIAssistantEmptyResponseError("OpenAI вернул пустой ответ.")

    def _format_http_error(self, exc: urllib.error.HTTPError) -> str:
        try:
            raw = exc.read().decode("utf-8")
            data = json.loads(raw)
            message = data.get("error", {}).get("message")
            if message:
                return message
        except Exception:
            pass
        return f"OpenAI вернул ошибку {exc.code}."


openai_assistant_service = OpenAIAssistantService()
