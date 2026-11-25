"""로컬 캘린더 서버 (표준 라이브러리만 사용).

- calendar.html 을 서빙한다.
- data/plans.json 파일에 계획 데이터를 읽고 쓴다.
- 실행하면 자동으로 기본 브라우저를 연다.

사용법:
    python server.py
"""

import json
import os
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST = "127.0.0.1"
PORT = 8765


def resource_dir():
    """번들된 리소스(calendar.html)가 있는 폴더.

    PyInstaller exe 로 실행되면 임시 해제 폴더(_MEIPASS),
    평소 python 실행이면 이 스크립트 폴더.
    """
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def app_dir():
    """데이터(plans.json)를 읽고 쓸 폴더.

    exe 로 실행되면 exe 가 놓인 실제 폴더,
    평소 python 실행이면 이 스크립트 폴더.
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = app_dir()
DATA_DIR = os.path.join(BASE_DIR, "data")
DATA_FILE = os.path.join(DATA_DIR, "plans.json")
HTML_FILE = os.path.join(resource_dir(), "calendar.html")


def ensure_data_file():
    """data 폴더와 plans.json 이 없으면 만든다."""
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)


def read_plans():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def write_plans(data):
    # 임시 파일에 먼저 쓰고 교체해서 쓰다가 깨지는 일을 막는다.
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DATA_FILE)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # 콘솔 로그 끄기

    def _send(self, code, body, content_type="application/json"):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type + "; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html", "/calendar.html"):
            try:
                with open(HTML_FILE, "rb") as f:
                    self._send(200, f.read(), "text/html")
            except FileNotFoundError:
                self._send(404, "calendar.html not found", "text/plain")
        elif self.path == "/api/plans":
            self._send(200, json.dumps(read_plans(), ensure_ascii=False))
        else:
            self._send(404, "Not found", "text/plain")

    def do_POST(self):
        if self.path == "/api/plans":
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length) if length else b"{}"
            try:
                data = json.loads(raw.decode("utf-8"))
                if not isinstance(data, dict):
                    raise ValueError
            except (json.JSONDecodeError, ValueError):
                self._send(400, json.dumps({"ok": False, "error": "bad json"}))
                return
            write_plans(data)
            self._send(200, json.dumps({"ok": True}))
        else:
            self._send(404, "Not found", "text/plain")


def main():
    ensure_data_file()
    url = f"http://{HOST}:{PORT}/"
    try:
        server = ThreadingHTTPServer((HOST, PORT), Handler)
    except OSError as e:
        print(f"서버를 시작할 수 없습니다 (포트 {PORT} 사용 중일 수 있음): {e}")
        sys.exit(1)

    print("캘린더 서버 실행 중:", url)
    print("데이터 파일:", DATA_FILE)
    print("종료하려면 이 창에서 Ctrl+C 를 누르세요.")

    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n서버를 종료합니다.")
        server.shutdown()


if __name__ == "__main__":
    main()
