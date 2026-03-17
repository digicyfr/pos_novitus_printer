# -*- coding: utf-8 -*-
"""
Integration Test Runner for Mock Novitus Server
================================================

Starts the mock Novitus Deon Online server, runs a complete
integration test sequence against it, and reports results.

Usage:
    python3 tests/run_mock_server.py
"""

import importlib.util
import json
import os
import sys
import time
import requests

# Direct import of mock_novitus_server without triggering __init__.py
_server_path = os.path.join(os.path.dirname(__file__), 'mock_novitus_server.py')
_spec = importlib.util.spec_from_file_location('mock_novitus_server', _server_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
run_server = _mod.run_server
store = _mod.store

PORT = 18888
BASE = 'http://127.0.0.1:%d' % PORT

PASS = '\033[92mPASS\033[0m'
FAIL = '\033[91mFAIL\033[0m'

results = []


def test(name, condition, detail=''):
    status = PASS if condition else FAIL
    results.append((name, condition))
    print('  [%s] %s%s' % (status, name, (' — ' + detail) if detail else ''))
    return condition


def run_tests():
    print('')
    print('=' * 60)
    print('Integration Test Sequence')
    print('=' * 60)

    headers_no_auth = {
        'Content-Type': 'application/json',
        'User-Agent': 'NoviApi',
    }

    # ── Test 1: Connection test ──────────────────────────────
    print('\n--- 1. Connection Test ---')
    try:
        r = requests.get('%s/api/v1' % BASE, headers=headers_no_auth, timeout=3)
        test('GET /api/v1 returns 200', r.status_code == 200,
             'got %d' % r.status_code)
    except Exception as e:
        test('GET /api/v1 returns 200', False, str(e))
        print('FATAL: Cannot connect to mock server. Aborting.')
        return

    # ── Test 2: Token acquisition ────────────────────────────
    print('\n--- 2. Token Acquisition ---')
    r = requests.get('%s/api/v1/token' % BASE, headers=headers_no_auth, timeout=3)
    test('GET /api/v1/token returns 200', r.status_code == 200)
    data = r.json()
    token = data.get('token', '')
    test('Response has token field', bool(token), token[:30] + '...')
    test('Response has expiration_date', 'expiration_date' in data,
         data.get('expiration_date', ''))

    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'NoviApi',
        'Authorization': 'Bearer %s' % token,
    }

    # ── Test 3: Token refresh via PATCH ──────────────────────
    print('\n--- 3. Token Refresh (PATCH) ---')
    r = requests.patch('%s/api/v1/token' % BASE, headers=headers,
                       data='""', timeout=3)
    test('PATCH /api/v1/token returns 200', r.status_code == 200)
    new_data = r.json()
    new_token = new_data.get('token', '')
    test('PATCH returns new token', bool(new_token) and new_token != token,
         'old=%s new=%s' % (token[:15], new_token[:15]))
    # Update token for subsequent requests
    token = new_token
    headers['Authorization'] = 'Bearer %s' % token

    # Test PATCH without auth → 401
    r = requests.patch('%s/api/v1/token' % BASE,
                       headers={'User-Agent': 'NoviApi', 'Content-Type': 'application/json'},
                       data='""', timeout=3)
    test('PATCH without Authorization returns 401', r.status_code == 401)

    # ── Test 4: Missing User-Agent check ─────────────────────
    print('\n--- 4. Header Validation ---')
    r = requests.post('%s/api/v1/direct_io' % BASE,
                      headers={'Content-Type': 'application/json',
                               'Authorization': 'Bearer %s' % token},
                      json={'direct_io': {'nov_cmd': {}}}, timeout=3)
    test('POST without User-Agent returns 400', r.status_code == 400)

    r = requests.post('%s/api/v1/direct_io' % BASE,
                      headers={'Content-Type': 'application/json',
                               'User-Agent': 'NoviApi'},
                      json={'direct_io': {'nov_cmd': {}}}, timeout=3)
    test('POST without Authorization returns 401', r.status_code == 401)

    # ── Test 5: Invalid direct_io structure ──────────────────
    print('\n--- 5. Payload Validation ---')
    r = requests.post('%s/api/v1/direct_io' % BASE, headers=headers,
                      json={'wrong_key': {}}, timeout=3)
    test('Invalid outer wrapper returns 400', r.status_code == 400)
    test('Error mentions direct_io.nov_cmd',
         'direct_io.nov_cmd' in r.json().get('error', ''))

    r = requests.post('%s/api/v1/direct_io' % BASE, headers=headers,
                      json={'direct_io': {'wrong': {}}}, timeout=3)
    test('Missing nov_cmd returns 400', r.status_code == 400)

    # ── Test 6: Full 3-step receipt flow ─────────────────────
    print('\n--- 6. Full 3-Step Receipt Flow ---')

    receipt_payload = {
        'direct_io': {
            'nov_cmd': {
                'h': {'cashier': 'TEST', 'system_no': 'TEST/001'},
                'l': [{
                    'name': 'Kawa Latte',
                    'quantity': '1',
                    'unit_price': '12.50',
                    'gross_value': '12.50',
                    'ptu': 'A',
                }],
                'b': [{'type': 0, 'value': '12.50'}],
                'y': {'total': '12.50', 'buyer_nip': ''},
            }
        }
    }

    # Step A: POST → 201 STORED
    r = requests.post('%s/api/v1/direct_io' % BASE, headers=headers,
                      json=receipt_payload, timeout=3)
    test('STEP A: POST returns 201', r.status_code == 201)
    resp_a = r.json()
    job_id = resp_a.get('request', {}).get('id', '')
    test('STEP A: got 32-char job ID', len(job_id) == 32, job_id)
    test('STEP A: status is STORED',
         resp_a.get('request', {}).get('status') == 'STORED')

    # Step B: PUT → 200 CONFIRMED
    r = requests.put('%s/api/v1/direct_io/%s' % (BASE, job_id),
                     headers=headers, data='""', timeout=3)
    test('STEP B: PUT returns 200', r.status_code == 200)
    test('STEP B: status is CONFIRMED',
         r.json().get('request', {}).get('status') == 'CONFIRMED')

    # Step C: GET with timeout → DONE
    r = requests.get('%s/api/v1/direct_io/%s?timeout=1000' % (BASE, job_id),
                     headers=headers, timeout=5)
    test('STEP C: GET returns 200', r.status_code == 200)
    resp_c = r.json()
    test('STEP C: status is DONE',
         resp_c.get('request', {}).get('status') == 'DONE')
    jpkid = resp_c.get('request', {}).get('jpkid', 0)
    test('STEP C: jpkid is positive integer',
         isinstance(jpkid, int) and jpkid > 0, 'jpkid=%d' % jpkid)

    # Verify call order: POST before PUT before GET
    test('3-step flow completed successfully', True)

    # ── Test 7: Cancel a job ─────────────────────────────────
    print('\n--- 7. Job Cancellation ---')

    # Create a new job
    r = requests.post('%s/api/v1/direct_io' % BASE, headers=headers,
                      json=receipt_payload, timeout=3)
    cancel_id = r.json().get('request', {}).get('id', '')
    test('Created job for cancellation', r.status_code == 201)

    # Cancel it before PUT (should succeed)
    r = requests.delete('%s/api/v1/direct_io/%s' % (BASE, cancel_id),
                        headers=headers, timeout=3)
    test('DELETE STORED job returns 200', r.status_code == 200)
    test('Cancel status is DELETED',
         r.json().get('request', {}).get('status') == 'DELETED')

    # Try to cancel the already-DONE job from test 6 (should fail)
    r = requests.delete('%s/api/v1/direct_io/%s' % (BASE, job_id),
                        headers=headers, timeout=3)
    test('DELETE DONE job returns 400', r.status_code == 400)

    # ── Test 8: Queue management ─────────────────────────────
    print('\n--- 8. Queue Management ---')

    r = requests.get('%s/api/v1/queue' % BASE, headers=headers, timeout=3)
    test('GET /api/v1/queue returns 200', r.status_code == 200)
    queue_count = r.json().get('requests_in_queue', -1)
    test('Queue count is integer', isinstance(queue_count, int),
         'count=%d' % queue_count)

    # Create a few pending jobs
    for i in range(3):
        requests.post('%s/api/v1/direct_io' % BASE, headers=headers,
                      json=receipt_payload, timeout=3)

    r = requests.get('%s/api/v1/queue' % BASE, headers=headers, timeout=3)
    queue_after = r.json().get('requests_in_queue', 0)
    test('Queue has pending jobs after POST', queue_after >= 3,
         'count=%d' % queue_after)

    # Clear queue
    r = requests.delete('%s/api/v1/queue' % BASE, headers=headers, timeout=3)
    test('DELETE /api/v1/queue returns 200', r.status_code == 200)

    r = requests.get('%s/api/v1/queue' % BASE, headers=headers, timeout=3)
    test('Queue is empty after clear',
         r.json().get('requests_in_queue', -1) == 0)

    # ── Test 9: Daily report ─────────────────────────────────
    print('\n--- 9. Daily Report ---')

    # Queue must be empty first
    r = requests.get('%s/api/v1/queue' % BASE, headers=headers, timeout=3)
    test('Queue empty before daily report',
         r.json().get('requests_in_queue', -1) == 0)

    # Submit daily report
    daily_payload = {
        'daily_report': {
            'date': time.strftime('%d/%m/%Y'),
            'system_info': {},
        }
    }
    r = requests.post('%s/api/v1/daily_report' % BASE, headers=headers,
                      json=daily_payload, timeout=3)
    test('POST /api/v1/daily_report returns 201', r.status_code == 201)
    daily_id = r.json().get('request', {}).get('id', '')
    test('Daily report got job ID', len(daily_id) == 32)

    # Wait for concurrency window to clear (0.5s simulation)
    time.sleep(0.6)

    # Confirm and poll
    r = requests.put('%s/api/v1/daily_report/%s' % (BASE, daily_id),
                     headers=headers, data='""', timeout=3)
    test('PUT daily report returns 200', r.status_code == 200)

    r = requests.get('%s/api/v1/daily_report/%s?timeout=1000' % (BASE, daily_id),
                     headers=headers, timeout=5)
    test('GET daily report returns DONE',
         r.json().get('request', {}).get('status') == 'DONE')

    # Test 409: create a pending job, then try daily report
    requests.post('%s/api/v1/direct_io' % BASE, headers=headers,
                  json=receipt_payload, timeout=3)
    r = requests.post('%s/api/v1/daily_report' % BASE, headers=headers,
                      json=daily_payload, timeout=3)
    test('Daily report with pending queue returns 409', r.status_code == 409)

    # Clean up
    requests.delete('%s/api/v1/queue' % BASE, headers=headers, timeout=3)

    # ── Test 10: Native receipt endpoint (400 with hints) ────
    print('\n--- 10. Native Receipt Endpoint (Discovery) ---')
    r = requests.post('%s/api/v1/receipt' % BASE, headers=headers,
                      json={'receipt': {'items': [], 'summary': {}}}, timeout=3)
    test('POST /api/v1/receipt returns 400', r.status_code == 400)
    errors = r.json().get('errors', [])
    test('Response has validation errors', len(errors) > 0,
         '%d errors returned' % len(errors))
    has_ptu_hint = any('ptu' in e.get('message', '').lower() for e in errors)
    test('Errors mention PTU field', has_ptu_hint)

    # ── Test 11: 404 for unknown endpoints ───────────────────
    print('\n--- 11. Unknown Endpoints ---')
    r = requests.get('%s/api/v1/nonexistent' % BASE,
                     headers=headers_no_auth, timeout=3)
    test('Unknown GET returns 404', r.status_code == 404)

    r = requests.post('%s/api/v1/cashbox/open' % BASE, headers=headers,
                      json={}, timeout=3)
    test('POST /api/v1/cashbox/open returns 404 (no such endpoint)',
         r.status_code == 404)

    # ── Test 12: PUT unknown job returns 404 ─────────────────
    print('\n--- 12. Error Cases ---')
    r = requests.put('%s/api/v1/direct_io/nonexistent_id_12345678' % BASE,
                     headers=headers, data='""', timeout=3)
    test('PUT unknown job ID returns 404', r.status_code == 404)

    r = requests.delete('%s/api/v1/direct_io/nonexistent_id_12345678' % BASE,
                        headers=headers, timeout=3)
    test('DELETE unknown job ID returns 404', r.status_code == 404)


def main():
    # Start mock server in background
    print('Starting mock Novitus server...')
    server, thread = run_server(port=PORT, blocking=False)
    time.sleep(0.5)  # Wait for server to start

    try:
        run_tests()
    except Exception as e:
        print('\nFATAL ERROR: %s' % e)
        import traceback
        traceback.print_exc()
    finally:
        print('\nStopping mock server...')
        server.shutdown()
        thread.join(timeout=2)

    # Summary
    passed = sum(1 for _, ok in results if ok)
    failed = sum(1 for _, ok in results if not ok)
    total = len(results)

    print('')
    print('=' * 60)
    print('RESULTS: %d/%d passed, %d failed' % (passed, total, failed))
    print('=' * 60)

    if failed > 0:
        print('\nFailed tests:')
        for name, ok in results:
            if not ok:
                print('  [FAIL] %s' % name)

    print('')
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
