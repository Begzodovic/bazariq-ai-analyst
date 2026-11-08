"""BazarIQ public judge-friendly server; read-only analytical backend."""
import argparse
import json
import os
import sqlite3
import threading
import traceback
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from analyst import Analyst
from database import Register
from provider import Provider, ProviderError, load_env
from translation import translate_items

ROOT = Path(__file__).resolve().parent


def friendly_failure(status, language="uz"):
    """Distinguish an execution failure from genuine absence of register data."""
    ru = language == "ru"
    if status in (429,):
        return ("Сейчас много запросов. Повторите попытку чуть позже." if ru else
                "Hozir so‘rovlar ko‘p. Birozdan keyin qayta urinib ko‘ring.")
    if status in (503, 504):
        return ("Сейчас AI не ответил. Попробуйте в новом чате или повторите позже." if ru else
                "Hozir AI xizmatidan javob olinmadi. Yangi chatda sinab ko‘rishingiz mumkin, xizmat ishlamasa keyinroq urinib ko‘ring.")
    return ("Сейчас не удалось проверить расчёт по реестру. Попробуйте новый чат или уточните вопрос." if ru else
            "Hozir javobni reyestrdan tekshirib bo‘lmadi. Yangi chatda sinab ko‘ring yoki savolni aniqlashtiring.")


class Handler(BaseHTTPRequestHandler):
    # Public demo: no Basic Auth, account, or installation required.
    # Gemini key is read only from server environment, never sent to clients.

    def reply(self, code, payload, mime="application/json"):
        body = (json.dumps(payload,ensure_ascii=False,allow_nan=False) if mime == "application/json" else payload).encode("utf8")
        self.send_response(code)
        self.send_header("Content-Type", mime + "; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options","nosniff")
        self.send_header("Cache-Control","no-store, max-age=0")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        agent = self.server.agent
        if self.path == "/health":
            p = agent.provider
            self.reply(200, {"ok":True,"database_exists":True,"provider":p.name,"model":p.model,
                           "configured":bool(p.key and p.model),"verified":p.verified,
                           "coverage":agent.db.context["deal_date_coverage"]})
        elif self.path == "/":
            self.reply(200, self.server.page, "text/html")
        else:
            self.reply(404,{"error":"404"})

    def do_POST(self):
        if self.path not in ("/api/ask", "/api/translate"):
            return self.reply(404,{"error":"404"})
        local_hosts = {f"localhost:{self.server.server_port}", f"127.0.0.1:{self.server.server_port}"}
        if os.getenv("BAZARIQ_PUBLIC", "0") != "1" and self.headers.get("Host", "").lower() not in local_hosts:
            return self.reply(403,{"error":"Localhost required"})
        # For public mode, reject explicit cross-origin browser requests.
        origin = self.headers.get("Origin", "")
        if origin and os.getenv("BAZARIQ_PUBLIC", "0") == "1":
            expected_origin = "https://" + self.headers.get("Host", "")
            if origin != expected_origin:
                return self.reply(403,{"error":"Cross-origin requests denied"})
        if self.headers.get_content_type() != "application/json" or self.headers.get("Sec-Fetch-Site") == "cross-site":
            return self.reply(415,{"error":"Local application/json request required"})
        # Bound abuse of the public Gemini-backed endpoint without requiring login.
        # Shared fixed-window limit deliberately uses server-wide requests because
        # reverse proxies can present the same remote address for multiple judges.
        with self.server.rate_lock:
            now = time.monotonic()
            while self.server.recent_requests and self.server.recent_requests[0] < now - 60:
                self.server.recent_requests.popleft()
            if len(self.server.recent_requests) >= self.server.rate_per_minute:
                return self.reply(429,{"status":"error","error":friendly_failure(429),"rows":[]})
            self.server.recent_requests.append(now)
        if not self.server.slots.acquire(blocking=False):
            return self.reply(429,{"error":"Band / Сервер занят"})
        try:
            length = int(self.headers.get("Content-Length","0"))
            if not 1 <= length <= 64000:
                return self.reply(413,{"error":"1–64000 bytes"})
            obj = json.loads(self.rfile.read(length))
            if not isinstance(obj,dict):
                raise ValueError("JSON object required")
            if self.path == "/api/translate":
                language = obj.get("lang")
                translated = translate_items(obj.get("items"), language, self.server.agent.provider)
                return self.reply(200, {"items": translated, "lang": language})
            request_lang = obj.get("lang") if obj.get("lang") in ("uz", "ru") else None
            result = self.server.agent.ask(obj.get("question"), request_lang, obj.get("conversation"))
            if request_lang:
                result["lang"] = request_lang
            if result.get("status") == "error":
                # Do not mistake a failed SQL check for an empty register result.
                diagnostic = result.get("diagnostic", "calculation")
                print(f"BazarIQ request validation failed: {diagnostic}", flush=True)
                result["error"] = friendly_failure(422, obj.get("lang") if obj.get("lang") in ("uz", "ru") else result.get("lang", "uz"))
            self.reply(422 if result["status"]=="error" else 200,result)
        except ProviderError as exc:
            print(f"BazarIQ provider unavailable: {type(exc).__name__}: {exc}",flush=True)
            self.reply(503,{"status":"provider_error","error":str(exc),"rows":[]})
        except (ValueError, UnicodeError) as exc:
            self.reply(400,{"error":str(exc)})
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:
            traceback.print_exc()
            self.reply(500,{"error":"Ichki xato / Внутренняя ошибка"})
        finally:
            self.server.slots.release()


def make_server(register, provider, port):
    address = "0.0.0.0" if os.getenv("BAZARIQ_PUBLIC", "0") == "1" else "127.0.0.1"
    http = ThreadingHTTPServer((address,port),Handler)
    http.agent = Analyst(register,provider)
    http.slots = threading.BoundedSemaphore(3)
    http.rate_lock = threading.Lock()
    http.recent_requests = deque()
    http.rate_per_minute = max(5,min(120,int(os.getenv("BAZARIQ_RATE_PER_MINUTE","30"))))
    http.page = (ROOT/"index.html").read_text(encoding="utf8")
    return http


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--list-models",action="store_true")
    group.add_argument("--check-provider",action="store_true")
    args = parser.parse_args()
    load_env(ROOT)
    p = Provider()
    if args.list_models:
        print("\n".join(p.models()))
        return
    if args.check_provider:
        print(p.name, p.check(), "OK")
        return
    db = Register(ROOT/"uzex.db")
    with make_server(db,p,int(os.getenv("PORT","8000"))) as server:
        print(f"BazarIQ listening on port {server.server_port}",flush=True)
        server.serve_forever()


if __name__ == "__main__":
    try:
        main()
    except (ProviderError, sqlite3.Error, OSError, ValueError) as exc:
        raise SystemExit(str(exc))
