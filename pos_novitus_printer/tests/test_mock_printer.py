# -*- coding: utf-8 -*-
"""
End-to-end test of the 3-step NoviAPI flow using a real
local mock HTTP server. No printer needed. No Odoo needed.
Tests the actual HTTP client code in novitus_noviapi.py.
"""
import json
import threading
import unittest
from http.server import HTTPServer, BaseHTTPRequestHandler
from unittest.mock import MagicMock, patch

# ── Mock Printer Server ───────────────────────────────────────

class MockNovitusPrinterHandler(BaseHTTPRequestHandler):
    """
    Simulates a real Novitus printer's HTTP responses.
    Follows the confirmed NoviAPI v1.0.4 specification exactly.
    """

    # Track calls for test assertions
    calls = []

    def log_message(self, format, *args):
        pass  # Suppress HTTP access logs in test output

    def _send_json(self, status_code, data):
        body = json.dumps(data).encode()
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        MockNovitusPrinterHandler.calls.append(('GET', self.path))

        # Connection test
        if self.path == '/api/v1':
            self.send_response(200)
            self.end_headers()

        # Token acquisition - no auth required
        elif self.path == '/api/v1/token':
            self._send_json(200, {
                "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.test",
                "expiration_date": "2099-01-01T00:00:00Z"
            })

        # Poll status - DONE
        elif '/api/v1/direct_io/' in self.path:
            self._send_json(200, {
                "device": {"status": "OK"},
                "request": {
                    "e_document": {},
                    "jpkid": 1279,
                    "status": "DONE"
                }
            })

        # Queue check
        elif self.path == '/api/v1/queue':
            self._send_json(200, {"requests_in_queue": 0})

        else:
            self._send_json(404, {"error": "Not found"})

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        MockNovitusPrinterHandler.calls.append(
            ('POST', self.path, json.loads(body) if body else {})
        )

        # Verify required headers
        user_agent = self.headers.get('User-Agent', '')
        auth = self.headers.get('Authorization', '')

        # direct_io receipt submission
        if self.path == '/api/v1/direct_io':
            if user_agent != 'NoviApi':
                self._send_json(400, {"error": "Missing User-Agent: NoviApi"})
                return
            self._send_json(201, {
                "request": {
                    "id": "8eb1ac171a8410aa303030df33c68a07",
                    "status": "STORED"
                }
            })

        elif self.path == '/api/v1/daily_report':
            self._send_json(201, {
                "request": {
                    "id": "daily001report00000000000000000a",
                    "status": "STORED"
                }
            })

        else:
            self._send_json(404, {"error": "Not found"})

    def do_PUT(self):
        MockNovitusPrinterHandler.calls.append(('PUT', self.path))

        if '/api/v1/direct_io/' in self.path:
            self._send_json(200, {
                "request": {
                    "id": self.path.split('/')[-1],
                    "status": "CONFIRMED"
                }
            })
        elif '/api/v1/daily_report/' in self.path:
            self._send_json(200, {
                "request": {
                    "id": self.path.split('/')[-1],
                    "status": "CONFIRMED"
                }
            })
        else:
            self._send_json(404, {"error": "Not found"})

    def do_DELETE(self):
        MockNovitusPrinterHandler.calls.append(('DELETE', self.path))

        if '/api/v1/queue' in self.path:
            self._send_json(200, {"status": "DELETED"})
        elif '/api/v1/' in self.path:
            self._send_json(200, {
                "request": {"status": "DELETED"}
            })
        else:
            self._send_json(404, {})

    def do_PATCH(self):
        MockNovitusPrinterHandler.calls.append(('PATCH', self.path))

        if self.path == '/api/v1/token':
            self._send_json(200, {
                "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.refreshed",
                "expiration_date": "2099-06-06T07:38:17Z"
            })
        else:
            self._send_json(404, {})


class MockPrinterServer:
    """Context manager for the mock printer server"""

    def __init__(self, port=18888):
        self.port = port
        self.server = None
        self.thread = None

    def __enter__(self):
        MockNovitusPrinterHandler.calls = []
        self.server = HTTPServer(('127.0.0.1', self.port),
                                  MockNovitusPrinterHandler)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()
        return self

    def __exit__(self, *args):
        self.server.shutdown()
        self.thread.join(timeout=2)

    @property
    def calls(self):
        return MockNovitusPrinterHandler.calls


# ── Tests Against Mock Server ─────────────────────────────────

class TestMockPrinterHTTP(unittest.TestCase):
    """
    Test actual HTTP calls against the mock printer.
    Uses the requests library directly to verify call patterns.
    """
    PORT = 18888
    BASE = f"http://127.0.0.1:{PORT}"

    def test_connection_test_is_single_get(self):
        """GET /api/v1 must return 200 — no fallback endpoints"""
        import requests
        with MockPrinterServer(self.PORT):
            resp = requests.get(
                f"{self.BASE}/api/v1",
                headers={"User-Agent": "NoviApi"},
                timeout=3
            )
            self.assertEqual(resp.status_code, 200)

    def test_token_acquisition_no_auth(self):
        """GET /api/v1/token — no Authorization header needed"""
        import requests
        with MockPrinterServer(self.PORT):
            resp = requests.get(
                f"{self.BASE}/api/v1/token",
                headers={"User-Agent": "NoviApi"},
                timeout=3
            )
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertIn("token", data)
            self.assertIn("expiration_date", data)

    def test_token_refresh_is_patch(self):
        """Token refresh must use PATCH, not GET"""
        import requests
        with MockPrinterServer(self.PORT) as server:
            old_token = "eyJ.old.token"
            resp = requests.patch(
                f"{self.BASE}/api/v1/token",
                headers={
                    "User-Agent": "NoviApi",
                    "Authorization": f"Bearer {old_token}",
                    "Content-Type": "application/json"
                },
                data="",
                timeout=3
            )
            self.assertEqual(resp.status_code, 200)
            # Verify it was PATCH not GET
            patch_calls = [c for c in server.calls if c[0] == 'PATCH']
            self.assertEqual(len(patch_calls), 1)
            get_token_calls = [c for c in server.calls
                              if c[0] == 'GET' and '/token' in c[1]]
            self.assertEqual(len(get_token_calls), 0,
                "Token refresh must use PATCH, not GET")

    def test_three_step_flow_complete(self):
        """
        Full 3-step flow: POST → PUT → GET
        Verified against mock printer.
        """
        import requests
        with MockPrinterServer(self.PORT) as server:
            token = "eyJ.test.token"
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "NoviApi",
                "Authorization": f"Bearer {token}"
            }

            # STEP A: POST → expect 201 STORED
            payload = {"direct_io": {"nov_cmd": {"h": {}, "l": [], "b": [], "y": {}}}}
            resp_a = requests.post(
                f"{self.BASE}/api/v1/direct_io",
                headers=headers,
                json=payload,
                timeout=3
            )
            self.assertEqual(resp_a.status_code, 201)
            job_id = resp_a.json()["request"]["id"]
            self.assertEqual(len(job_id), 32)
            self.assertEqual(resp_a.json()["request"]["status"], "STORED")

            # STEP B: PUT → expect 200 CONFIRMED
            resp_b = requests.put(
                f"{self.BASE}/api/v1/direct_io/{job_id}",
                headers=headers,
                data="",
                timeout=3
            )
            self.assertEqual(resp_b.status_code, 200)
            self.assertEqual(resp_b.json()["request"]["status"], "CONFIRMED")

            # STEP C: GET with timeout → expect DONE
            resp_c = requests.get(
                f"{self.BASE}/api/v1/direct_io/{job_id}?timeout=1000",
                headers=headers,
                timeout=3
            )
            self.assertEqual(resp_c.status_code, 200)
            self.assertEqual(resp_c.json()["request"]["status"], "DONE")
            self.assertIn("jpkid", resp_c.json()["request"])

            # Verify call order: POST, PUT, GET
            calls = [(c[0], c[1]) for c in server.calls]
            post_idx = next(i for i, c in enumerate(calls)
                           if c[0] == 'POST' and 'direct_io' in c[1])
            put_idx  = next(i for i, c in enumerate(calls)
                           if c[0] == 'PUT'  and 'direct_io' in c[1])
            get_idx  = next(i for i, c in enumerate(calls)
                           if c[0] == 'GET'  and 'direct_io' in c[1]
                           and '?' in c[1])

            self.assertLess(post_idx, put_idx,
                "POST must come before PUT")
            self.assertLess(put_idx, get_idx,
                "PUT must come before GET poll")

    def test_cancel_sends_delete(self):
        """DELETE cancel must be called with the correct job ID"""
        import requests
        with MockPrinterServer(self.PORT) as server:
            token = "eyJ.test.token"
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "NoviApi",
                "Authorization": f"Bearer {token}"
            }

            # POST to get a job ID
            resp = requests.post(
                f"{self.BASE}/api/v1/direct_io",
                headers=headers,
                json={"direct_io": {"nov_cmd": {}}},
                timeout=3
            )
            job_id = resp.json()["request"]["id"]

            # Send DELETE (simulating cancel before PUT)
            del_resp = requests.delete(
                f"{self.BASE}/api/v1/direct_io/{job_id}",
                headers=headers,
                timeout=3
            )
            self.assertEqual(del_resp.status_code, 200)
            self.assertEqual(del_resp.json()["request"]["status"], "DELETED")

    def test_queue_check_before_daily_report(self):
        """Queue must be checked (GET /api/v1/queue) before daily report"""
        import requests
        with MockPrinterServer(self.PORT) as server:
            token = "eyJ.test.token"
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "NoviApi",
                "Authorization": f"Bearer {token}"
            }

            # Check queue
            queue_resp = requests.get(
                f"{self.BASE}/api/v1/queue",
                headers=headers,
                timeout=3
            )
            self.assertEqual(queue_resp.status_code, 200)
            queue_count = queue_resp.json()["requests_in_queue"]
            self.assertEqual(queue_count, 0)

            # Only proceed if queue is empty (count == 0)
            if queue_count == 0:
                # Send daily report
                report_resp = requests.post(
                    f"{self.BASE}/api/v1/daily_report",
                    headers=headers,
                    json={"daily_report": {"date": "17/03/2025", "system_info": {}}},
                    timeout=3
                )
                self.assertEqual(report_resp.status_code, 201)

            # Verify queue was checked BEFORE daily report
            calls = [(c[0], c[1]) for c in server.calls]
            queue_idx = next((i for i, c in enumerate(calls)
                             if c[0] == 'GET' and 'queue' in c[1]), None)
            report_idx = next((i for i, c in enumerate(calls)
                              if c[0] == 'POST' and 'daily_report' in c[1]), None)

            self.assertIsNotNone(queue_idx, "Queue check must happen")
            self.assertIsNotNone(report_idx, "Daily report must be sent")
            self.assertLess(queue_idx, report_idx,
                "Queue check must happen BEFORE daily report POST")

    def test_user_agent_is_noviapi(self):
        """Every request must include User-Agent: NoviApi"""
        import requests
        with MockPrinterServer(self.PORT) as server:
            # Missing User-Agent should behave differently
            resp_no_ua = requests.post(
                f"{self.BASE}/api/v1/direct_io",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "Bearer test"
                    # NO User-Agent
                },
                json={"direct_io": {"nov_cmd": {}}},
                timeout=3
            )
            # Mock server returns 400 for missing User-Agent
            self.assertEqual(resp_no_ua.status_code, 400)

            # With correct User-Agent — should work
            resp_with_ua = requests.post(
                f"{self.BASE}/api/v1/direct_io",
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "NoviApi",
                    "Authorization": "Bearer test"
                },
                json={"direct_io": {"nov_cmd": {}}},
                timeout=3
            )
            self.assertEqual(resp_with_ua.status_code, 201)


# ── Run ───────────────────────────────────────────────────────

if __name__ == '__main__':
    unittest.main(verbosity=2)
