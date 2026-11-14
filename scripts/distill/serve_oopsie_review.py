"""Range-capable local video server with append-only Markdown review notes."""
import argparse
from datetime import datetime, timezone
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tacc"))
from serve_flora_review import ReviewHandler


class OopsieReviewHandler(ReviewHandler):
    def send_head(self):
        # Review pages change as teacher results and UI fixes are published.
        # Do not let a cached document keep an obsolete embedded label snapshot.
        path = self.path.split('?', 1)[0]
        if path.endswith(('.html', '/')):
            for name in ('If-Modified-Since', 'If-None-Match'):
                if name in self.headers:
                    del self.headers[name]
        return super().send_head()

    def end_headers(self):
        if self.path.split('?', 1)[0].endswith(('.html', '/')):
            self.send_header('Cache-Control', 'no-store, max-age=0')
        super().end_headers()

    def do_POST(self):
        if self.path != "/review-notes":
            self.send_error(404)
            return
        origin = self.headers.get("Origin")
        expected = f"http://127.0.0.1:{self.server.server_port}"
        if origin and origin != expected:
            self.send_error(403)
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            size = 0
        if not 0 < size <= 1024 * 1024 or not self.headers.get("Content-Type", "").startswith("text/markdown"):
            self.send_error(400, "A Markdown review note is required")
            return
        try:
            content = self.rfile.read(size).decode("utf-8")
        except UnicodeDecodeError:
            self.send_error(400, "Markdown notes must be UTF-8")
            return
        folder = Path(self.directory) / "reviews"
        folder.mkdir(exist_ok=True)
        name = datetime.now(timezone.utc).strftime("review_%Y%m%dT%H%M%SZ_") + uuid.uuid4().hex[:8] + ".md"
        with (folder / name).open("x", encoding="utf-8", newline="") as stream:
            stream.write(content)
        body = ("reviews/" + name).encode("utf-8")
        self.send_response(201)
        self.send_header("Content-Type", "text/plain;charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8791)
    args = parser.parse_args()
    with ThreadingHTTPServer(("127.0.0.1", args.port), partial(OopsieReviewHandler, directory=str(args.directory.resolve()))) as server:
        print(f"Video review: http://127.0.0.1:{args.port}/review.html", flush=True)
        server.serve_forever()
