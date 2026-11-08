"""Explicit provider selection. No key is sent to the browser or logged."""
import json
import os
import re
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

PROVIDERS = {
    "gemini": ("Google Gemini", "GEMINI", "https://generativelanguage.googleapis.com/v1beta/openai"),
}


class ProviderError(RuntimeError):
    pass


class ModelFormatError(ProviderError):
    """A model responded, but its output was not a JSON object."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args):
        return None


def load_env(directory):
    path = Path(directory) / ".env"
    if path.is_file():
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            key, sep, value = line.strip().partition("=")
            if sep and re.fullmatch(r"[A-Z][A-Z0-9_]*", key.strip()):
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


class Provider:
    def __init__(self):
        self.id = "gemini"
        if self.id not in PROVIDERS:
            raise ProviderError("Only Google Gemini is supported")
        self.name, self.prefix, self.base = PROVIDERS[self.id]
        self.key = os.getenv(self.prefix + "_API_KEY", "").strip()
        self.model = os.getenv(self.prefix + "_MODEL", "").strip()
        self.lock = threading.Lock()
        self.deadline_local = threading.local()
        self.verified = False

    def request(self, endpoint, data=None):
        if not self.key:
            raise ProviderError(f"{self.name}: {self.prefix}_API_KEY kerak / требуется ключ.")
        body = None if data is None else json.dumps(data).encode()
        request = urllib.request.Request(self.base + endpoint, data=body, headers={
            "Authorization": "Bearer " + self.key, "Content-Type":"application/json",
            "User-Agent":"BazarIQ/3", "Accept":"application/json"})
        try:
            remaining=getattr(self.deadline_local,"deadline",time.monotonic()+3600)-time.monotonic()
            if remaining <= 1: raise ProviderError("AI request deadline exceeded")
            timeout=min(float(os.getenv("AI_TIMEOUT", "35")), remaining-0.5)
            with urllib.request.build_opener(NoRedirect).open(request, timeout=timeout) as response:
                return json.loads(response.read(2_000_000))
        except urllib.error.HTTPError as exc:
            hints = {400:"request/model", 401:"API key", 403:"access/region", 404:"model/endpoint",
                     402:"billing", 429:"quota/rate limit"}
            raise ProviderError(f"{self.name} · HTTP {exc.code} · {hints.get(exc.code,'provider')}") from None
        except (OSError, ValueError) as exc:
            raise ProviderError(f"{self.name} · {type(exc).__name__} · aloqa yoki javob / соединение или ответ") from None

    def models(self):
        data = self.request("/models")
        return sorted(str(item["id"]) for item in data.get("data", []) if isinstance(item, dict) and item.get("id"))

    def chat(self, system, payload, *, schema=None):
        if not self.key or not self.model:
            missing = "API_KEY" if not self.key else "MODEL"
            raise ProviderError(f"{self.name}: {self.prefix}_{missing} ni sozlang / укажите в .env")
        body = {"model": self.model, "messages": [
            {"role":"system", "content":system}, {"role":"user", "content":json.dumps(payload, ensure_ascii=False)}]}
        # Some OpenAI-compatible providers reject Gemini's json_schema dialect.
        # JSON is enforced by the system prompt and tolerant local parsing instead.
        if schema and self.id == "gemini" and os.getenv("GEMINI_JSON_SCHEMA", "0") == "1":
            body["response_format"] = {"type":"json_schema","json_schema":schema}
        body["temperature"] = 0
        data = self.request("/chat/completions",body)
        try:
            raw = data["choices"][0]["message"]["content"]
            if isinstance(raw,list):
                raw = "".join(str(x.get("text", "")) for x in raw if isinstance(x,dict))
            raw = raw.strip()
            if raw.startswith("```"):
                raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.I)
            try:
                obj = json.loads(raw)
            except ValueError:
                # Some models add a brief preamble despite the JSON instruction.
                decoder=json.JSONDecoder()
                start=raw.find("{")
                if start<0:raise
                obj,_=decoder.raw_decode(raw[start:])
            if not isinstance(obj, dict):
                raise ValueError()
            self.verified = True  # The selected model actually completed a request.
            return obj
        except (KeyError, IndexError, TypeError, AttributeError, ValueError):
            raise ModelFormatError(f"{self.name}: model JSON javob bermadi / неверный JSON модели.") from None

    def check(self):
        with self.lock:
            result = self.chat('Return just the JSON object {"ok":true}.', {"test":"connectivity"})
            if result.get("ok") is not True:
                self.verified = False
                raise ProviderError(f"{self.name}: model check failed / проверка модели не пройдена.")
        return self.model
