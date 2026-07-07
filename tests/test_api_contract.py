import asyncio
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

try:
    from shopify_ai_automation.api import app
except Exception:  # pragma: no cover
    app = None


async def asgi_request(method: str, path: str, body: dict | None = None) -> tuple[int, bytes]:
    raw_body = b"" if body is None else json.dumps(body).encode("utf-8")
    messages: list[dict] = []
    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode("ascii"),
        "query_string": b"",
        "headers": [(b"content-type", b"application/json")],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
        "root_path": "",
    }

    async def receive() -> dict:
        return {"type": "http.request", "body": raw_body, "more_body": False}

    async def send(message: dict) -> None:
        messages.append(message)

    await app(scope, receive, send)
    status = next(message["status"] for message in messages if message["type"] == "http.response.start")
    response_body = b"".join(message.get("body", b"") for message in messages if message["type"] == "http.response.body")
    return status, response_body


@unittest.skipIf(app is None, "ASGI app dependencies are not installed.")
class ApiContractTests(unittest.TestCase):
    def test_website_loads(self) -> None:
        status, body = asyncio.run(asgi_request("GET", "/"))

        self.assertEqual(status, 200)
        self.assertIn(b"Shopify AI Automation", body)

    def test_run_demo_returns_scored_actions(self) -> None:
        status, body = asyncio.run(asgi_request("POST", "/api/run-demo", {"provider": "mock"}))
        payload = json.loads(body)

        self.assertEqual(status, 200)
        self.assertEqual(payload["provider"], "mock")
        self.assertGreaterEqual(len(payload["actions"]), 3)
        self.assertIn("quality_score", payload)

    def test_compare_handles_missing_sarvam_key(self) -> None:
        status, body = asyncio.run(asgi_request("POST", "/api/compare", {}))
        payload = json.loads(body)

        self.assertEqual(status, 200)
        self.assertIn("mock", payload)
        self.assertIn("sarvam", payload)


if __name__ == "__main__":
    unittest.main()
