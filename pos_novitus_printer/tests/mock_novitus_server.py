# -*- coding: utf-8 -*-
"""
Mock Novitus Deon Online Fiscal Printer Server
===============================================

Simulates NoviAPI v1.0.4 firmware behaviour for testing
without real hardware. Implements the confirmed 3-step
command flow, token management, rate limiting, and
queue management.

Usage:
    python3 tests/mock_novitus_server.py

Runs on http://127.0.0.1:18888
"""

import json
import time
import uuid
import threading
from datetime import datetime, timedelta, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs


# ── Job Store ─────────────────────────────────────────────────

class JobStore:
    """Thread-safe store for tracking printer jobs."""

    def __init__(self):
        self._lock = threading.Lock()
        self._jobs = {}  # id -> {status, payload, created_at, confirmed_at}
        self._last_put_time = 0.0  # for 403 concurrency simulation
        self._token_request_count = 0
        self._current_token = None
        self._token_expiry = None
        self._jpk_counter = 1000

    def reset_token_counter(self):
        with self._lock:
            self._token_request_count = 0

    @property
    def token_request_count(self):
        with self._lock:
            return self._token_request_count

    def increment_token_count(self):
        with self._lock:
            self._token_request_count += 1
            return self._token_request_count

    def generate_token(self):
        with self._lock:
            ts = '%d.%06d' % (int(time.time()), int(time.time() * 1e6) % 1000000)
            self._current_token = 'eyJ.mock.token.%s' % ts
            self._token_expiry = (
                datetime.now(timezone.utc) + timedelta(minutes=20)
            ).strftime('%Y-%m-%dT%H:%M:%SZ')
            return self._current_token, self._token_expiry

    def invalidate_token(self):
        with self._lock:
            self._current_token = None
            self._token_expiry = None

    @property
    def current_token(self):
        with self._lock:
            return self._current_token

    def create_job(self, payload):
        with self._lock:
            job_id = uuid.uuid4().hex
            self._jobs[job_id] = {
                'status': 'STORED',
                'payload': payload,
                'created_at': time.time(),
                'confirmed_at': None,
            }
            return job_id

    def get_job(self, job_id):
        with self._lock:
            return self._jobs.get(job_id)

    def confirm_job(self, job_id):
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            now = time.time()
            # Simulate 403 concurrency: if another PUT within 0.5s
            if now - self._last_put_time < 0.5:
                return 'BUSY'
            self._last_put_time = now
            job['status'] = 'CONFIRMED'
            job['confirmed_at'] = now
            return 'CONFIRMED'

    def complete_job(self, job_id):
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            self._jpk_counter += 1
            job['status'] = 'DONE'
            job['jpkid'] = self._jpk_counter
            return self._jpk_counter

    def cancel_job(self, job_id):
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            if job['status'] in ('STORED', 'QUEUED'):
                job['status'] = 'DELETED'
                return 'DELETED'
            return 'INVALID'  # cannot cancel DONE/CONFIRMED

    def queue_count(self):
        with self._lock:
            return sum(
                1 for j in self._jobs.values()
                if j['status'] in ('STORED', 'QUEUED')
            )

    def clear_queue(self):
        with self._lock:
            to_delete = [
                jid for jid, j in self._jobs.items()
                if j['status'] in ('STORED', 'QUEUED')
            ]
            for jid in to_delete:
                self._jobs[jid]['status'] = 'DELETED'
            return len(to_delete)


# ── Global store ──────────────────────────────────────────────

store = JobStore()


# ── Request Handler ───────────────────────────────────────────

class NovitusDeonHandler(BaseHTTPRequestHandler):
    """Simulates Novitus Deon Online NoviAPI v1.0.4 firmware."""

    def log_message(self, format, *args):
        pass  # We do our own logging

    def _log_request(self, status_code, start_time):
        elapsed = (time.time() - start_time) * 1000
        ua = self.headers.get('User-Agent', '-')
        auth = self.headers.get('Authorization', '-')
        if auth and auth != '-':
            auth = auth[:15] + '***'
        print('[%s] %s -> %d (%.1fms)' % (
            self.command, self.path, status_code, elapsed))
        print('  Headers: {User-Agent: %s, Authorization: %s}' % (ua, auth))

    def _send_json(self, status_code, data, start_time=None):
        body = json.dumps(data).encode('utf-8')
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)
        if start_time:
            self._log_request(status_code, start_time)

    def _send_empty(self, status_code, start_time=None):
        self.send_response(status_code)
        self.send_header('Content-Length', 0)
        self.end_headers()
        if start_time:
            self._log_request(status_code, start_time)

    def _read_body(self):
        length = int(self.headers.get('Content-Length', 0))
        if length == 0:
            return None
        raw = self.rfile.read(length)
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return '__MALFORMED__'

    def _check_user_agent(self, start_time):
        """Returns True if User-Agent is valid, sends 400 if not."""
        ua = self.headers.get('User-Agent', '')
        if ua != 'NoviApi':
            self._send_json(400, {
                'error': 'Missing or invalid User-Agent header. Expected: NoviApi'
            }, start_time)
            return False
        return True

    def _check_auth(self, start_time):
        """Returns True if Authorization is valid, sends 401 if not."""
        auth = self.headers.get('Authorization', '')
        if not auth.startswith('Bearer '):
            self._send_json(401, {
                'error': 'Missing Authorization: Bearer {token} header'
            }, start_time)
            return False
        token_val = auth[7:]
        if store.current_token and token_val != store.current_token:
            self._send_json(401, {
                'error': 'Invalid or expired token'
            }, start_time)
            return False
        return True

    def _parse_path(self):
        """Parse URL path and query string."""
        parsed = urlparse(self.path)
        return parsed.path.rstrip('/'), parse_qs(parsed.query)

    # ── GET ───────────────────────────────────────────────────

    def do_GET(self):
        start = time.time()
        path, qs = self._parse_path()

        # GET /api/v1 — connection test (no auth required)
        if path == '/api/v1':
            self._send_empty(200, start)
            return

        # GET /api/v1/token — acquire new token (no auth required)
        if path == '/api/v1/token':
            count = store.increment_token_count()
            if count > 10:
                store.invalidate_token()
                self._send_json(429, {
                    'error': 'Too many token requests. '
                             'Reset from printer: [3 SERWIS]/[3.3.1 ZEROWANIE]/'
                             '[9 ZERUJ NOVIAPI]/[2 ODBLOKUJ]'
                }, start)
                print('  Token rate limit: %d/10 (EXCEEDED — token invalidated)' % count)
                return
            token, expiry = store.generate_token()
            self._send_json(200, {
                'token': token,
                'expiration_date': expiry,
            }, start)
            print('  Token rate limit: %d/10' % count)
            return

        # GET /api/v1/queue — check queue count
        if path == '/api/v1/queue':
            if not self._check_user_agent(start):
                return
            if not self._check_auth(start):
                return
            self._send_json(200, {
                'requests_in_queue': store.queue_count(),
            }, start)
            return

        # GET /api/v1/{endpoint}/{id}?timeout=N — poll job status
        parts = path.split('/')
        if len(parts) == 5 and parts[1] == 'api' and parts[2] == 'v1':
            endpoint = parts[3]
            job_id = parts[4]

            if not self._check_user_agent(start):
                return
            if not self._check_auth(start):
                return

            job = store.get_job(job_id)
            if not job:
                self._send_json(404, {
                    'error': 'Job ID not found: %s' % job_id
                }, start)
                return

            # Simulate processing time (0.3s)
            timeout_ms = int(qs.get('timeout', ['5000'])[0])
            time.sleep(0.3)

            # Auto-complete confirmed jobs
            if job['status'] == 'CONFIRMED':
                jpkid = store.complete_job(job_id)
                self._send_json(200, {
                    'device': {'status': 'OK'},
                    'request': {
                        'id': job_id,
                        'status': 'DONE',
                        'jpkid': jpkid,
                        'e_document': {},
                    }
                }, start)
                return

            # Return current status for non-confirmed jobs
            self._send_json(200, {
                'device': {'status': 'OK'},
                'request': {
                    'id': job_id,
                    'status': job['status'],
                    'jpkid': job.get('jpkid', 0),
                    'e_document': {},
                }
            }, start)
            return

        self._send_json(404, {'error': 'Not found'}, start)

    # ── POST ──────────────────────────────────────────────────

    def do_POST(self):
        start = time.time()
        path, qs = self._parse_path()

        if not self._check_user_agent(start):
            return

        body = self._read_body()
        if body == '__MALFORMED__':
            self._send_json(400, {
                'error': 'Malformed JSON body'
            }, start)
            return

        # Log body summary
        if isinstance(body, dict):
            print('  Body keys: %s' % list(body.keys()))

        # POST /api/v1/direct_io — submit command via serial protocol
        if path == '/api/v1/direct_io':
            if not self._check_auth(start):
                return
            if not isinstance(body, dict) or 'direct_io' not in body:
                self._send_json(400, {
                    'error': 'Invalid structure: expected direct_io.nov_cmd'
                }, start)
                return
            dio = body.get('direct_io', {})
            if not isinstance(dio, dict) or 'nov_cmd' not in dio:
                self._send_json(400, {
                    'error': 'Invalid structure: expected direct_io.nov_cmd'
                }, start)
                return
            job_id = store.create_job(body)
            self._send_json(201, {
                'request': {
                    'id': job_id,
                    'status': 'STORED',
                }
            }, start)
            return

        # POST /api/v1/receipt — native receipt (return 400 with field hints)
        if path == '/api/v1/receipt':
            if not self._check_auth(start):
                return
            # Simulate validation error revealing expected field names
            self._send_json(400, {
                'errors': [
                    {
                        'field': 'receipt',
                        'message': "Unknown top-level key 'receipt'. "
                                   "Expected keys: 'items', 'payments', 'header'."
                    },
                    {
                        'field': 'items[0].ptu',
                        'message': "Field 'ptu' is required for each item. "
                                   "Valid values: A, B, C, D, E, Z."
                    },
                    {
                        'field': 'items[0].gross',
                        'message': "Field 'gross' is required. "
                                   "Must equal round(price * qty, 2)."
                    },
                    {
                        'field': 'payments[0].type',
                        'message': "Field 'type' is required. "
                                   "Integer: 0=cash, 1=card, 2=cheque, "
                                   "3=voucher, 4=other, 5=credit, 8=transfer."
                    },
                ]
            }, start)
            return

        # POST /api/v1/daily_report — submit daily Z-report
        if path == '/api/v1/daily_report':
            if not self._check_auth(start):
                return
            # Check queue first — 409 if not empty
            if store.queue_count() > 0:
                self._send_json(409, {
                    'error': 'Daily report pending. Queue has %d jobs. '
                             'Clear queue before running daily report.' %
                             store.queue_count()
                }, start)
                return
            job_id = store.create_job(body or {})
            self._send_json(201, {
                'request': {
                    'id': job_id,
                    'status': 'STORED',
                }
            }, start)
            return

        # POST /api/v1/status — submit status query
        if path == '/api/v1/status':
            if not self._check_auth(start):
                return
            job_id = store.create_job(body or {})
            self._send_json(201, {
                'request': {
                    'id': job_id,
                    'status': 'STORED',
                }
            }, start)
            return

        self._send_json(404, {'error': 'Not found'}, start)

    # ── PUT ───────────────────────────────────────────────────

    def do_PUT(self):
        start = time.time()
        path, qs = self._parse_path()

        if not self._check_user_agent(start):
            return
        if not self._check_auth(start):
            return

        parts = path.split('/')
        if len(parts) != 5:
            self._send_json(404, {'error': 'Not found'}, start)
            return

        job_id = parts[4]
        result = store.confirm_job(job_id)

        if result is None:
            self._send_json(404, {
                'error': 'Job ID not found: %s' % job_id
            }, start)
        elif result == 'BUSY':
            self._send_json(403, {
                'error': 'Printer busy. Another command is being processed. '
                         'Retry after 1 second.'
            }, start)
        else:
            self._send_json(200, {
                'request': {
                    'id': job_id,
                    'status': 'CONFIRMED',
                }
            }, start)

    # ── DELETE ────────────────────────────────────────────────

    def do_DELETE(self):
        start = time.time()
        path, qs = self._parse_path()

        if not self._check_user_agent(start):
            return
        if not self._check_auth(start):
            return

        # DELETE /api/v1/queue — clear all pending jobs
        if path == '/api/v1/queue':
            count = store.clear_queue()
            self._send_json(200, {
                'status': 'DELETED',
                'cleared': count,
            }, start)
            return

        # DELETE /api/v1/{endpoint}/{id} — cancel specific job
        parts = path.split('/')
        if len(parts) == 5:
            job_id = parts[4]
            result = store.cancel_job(job_id)

            if result is None:
                self._send_json(404, {
                    'error': 'Job ID not found: %s' % job_id
                }, start)
            elif result == 'DELETED':
                self._send_json(200, {
                    'request': {
                        'id': job_id,
                        'status': 'DELETED',
                    }
                }, start)
            else:
                self._send_json(400, {
                    'error': 'Cannot cancel job in status %s. '
                             'Only STORED or QUEUED jobs can be cancelled.' %
                             store.get_job(job_id).get('status', 'UNKNOWN')
                }, start)
            return

        self._send_json(404, {'error': 'Not found'}, start)

    # ── PATCH ─────────────────────────────────────────────────

    def do_PATCH(self):
        start = time.time()
        path, qs = self._parse_path()

        # PATCH /api/v1/token — refresh token (does NOT count toward limit)
        if path == '/api/v1/token':
            auth = self.headers.get('Authorization', '')
            if not auth.startswith('Bearer '):
                self._send_json(401, {
                    'error': 'Authorization header required for token refresh'
                }, start)
                return
            token, expiry = store.generate_token()
            self._send_json(200, {
                'token': token,
                'expiration_date': expiry,
            }, start)
            print('  Token refreshed via PATCH (does NOT count toward limit)')
            return

        self._send_json(404, {'error': 'Not found'}, start)


# ── Server runner ─────────────────────────────────────────────

def run_server(port=18888, blocking=True):
    """Start the mock Novitus server."""
    server = HTTPServer(('127.0.0.1', port), NovitusDeonHandler)
    print('')
    print('=' * 60)
    print('Mock Novitus Deon Online running on http://127.0.0.1:%d' % port)
    print('Training mode: receipts accepted, NOT fiscally stored')
    print('Token rate limit: 10/hour (current: %d)' % store.token_request_count)
    print('Press Ctrl+C to stop')
    print('=' * 60)
    print('')

    if blocking:
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print('\nShutting down mock printer server...')
            server.shutdown()
    else:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server, thread


if __name__ == '__main__':
    run_server(port=18888, blocking=True)
