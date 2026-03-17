# -*- coding: utf-8 -*-
"""
Novitus NoviAPI REST Service
=============================

Communicates with Novitus online fiscal printers via the NoviAPI REST protocol.
Implements the verified 3-step command execution flow (POST → PUT → GET poll)
and uses direct_io with serial protocol commands for receipt construction.

Supported Printers:
- Novitus POINT (ONLINE 3.0)
- Novitus HD II Online (ONLINE 2.0)
- Novitus BONO Online
- Novitus DEON Online
"""

import logging
import time
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

import requests
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

NOVIAPI_ENDPOINTS = {
    'test':          '/api/v1',
    'token':         '/api/v1/token',
    'receipt':       '/api/v1/receipt',
    'invoice':       '/api/v1/invoice',
    'daily_report':  '/api/v1/daily_report',
    'status':        '/api/v1/status',
    'direct_io':     '/api/v1/direct_io',
    'nf_printout':   '/api/v1/nf_printout',
    'queue':         '/api/v1/queue',
    'configuration': '/api/v1/configuration',
    'graphic':       '/api/v1/graphic',
}

CONNECT_TEST_TIMEOUT_SECONDS = 5
API_TIMEOUT_SECONDS = 30
DEFAULT_POLL_TIMEOUT_MS = 5000
MAX_POLL_SECONDS = 30
TOKEN_REFRESH_BUFFER_MINUTES = 2

# Payment type integers from Novitus serial protocol (section 3.6.11)
PAYMENT_TYPE_CASH = 0
PAYMENT_TYPE_CARD = 1
PAYMENT_TYPE_CHEQUE = 2
PAYMENT_TYPE_VOUCHER = 3
PAYMENT_TYPE_OTHER = 4
PAYMENT_TYPE_CREDIT = 5
PAYMENT_TYPE_TRANSFER = 8


class NovitusNoviApi(models.AbstractModel):
    _name = 'novitus.noviapi'
    _description = 'Novitus NoviAPI REST Service'

    # ── URL construction ──────────────────────────────────────────────

    def _get_base_url(self, printer):
        """Build base URL: http(s)://IP:PORT"""
        if not printer.novitus_printer_ip:
            raise UserError(_('Novitus printer IP address is not configured.'))
        protocol = 'https' if printer.novitus_use_https else 'http'
        return '%s://%s:%s' % (protocol, printer.novitus_printer_ip, printer.novitus_printer_port or 8888)

    def _get_endpoint_url(self, printer, endpoint_key):
        """Build full endpoint URL from base URL + endpoint path."""
        base = self._get_base_url(printer)
        path = NOVIAPI_ENDPOINTS.get(endpoint_key)
        if not path:
            raise UserError(_('Unknown NoviAPI endpoint key: %s') % endpoint_key)
        return base + path

    # ── Token management ─────────────────────────────────────────────

    def _get_valid_token(self, printer):
        """
        Return a valid JWT token for the given printer.
        Strategy:
          1. If cached token expires in > TOKEN_REFRESH_BUFFER_MINUTES → return it
          2. If cached token expired or near-expired → PATCH to refresh
          3. If no cached token → GET new token
        """
        now = fields.Datetime.now()

        if printer.novitus_token_cache and printer.novitus_token_expiry:
            expiry = printer.novitus_token_expiry
            buffer = timedelta(minutes=TOKEN_REFRESH_BUFFER_MINUTES)

            if expiry > now + buffer:
                # Token is still valid with buffer
                return printer.novitus_token_cache

            # Token is expired or about to expire — refresh via PATCH
            _logger.info('Novitus token near expiry, refreshing via PATCH for printer %s',
                         printer.novitus_printer_ip)
            return self._refresh_token(printer)

        # No cached token — fetch a new one via GET
        _logger.info('No cached Novitus token, fetching new token for printer %s',
                     printer.novitus_printer_ip)
        return self._fetch_new_token(printer)

    def _fetch_new_token(self, printer):
        """GET /api/v1/token — no auth required.
        Rate limited: 10 per hour per printer. Exceeding cancels active token.
        """
        url = self._get_endpoint_url(printer, 'token')
        headers = self._get_headers(printer, include_auth=False)

        try:
            response = requests.get(url, headers=headers, timeout=API_TIMEOUT_SECONDS)
        except requests.exceptions.RequestException as e:
            raise UserError(
                _('Cannot connect to Novitus printer at %s: %s') % (url, str(e))
            )

        if response.status_code == 429:
            _logger.critical(
                'Novitus token rate limit exceeded for printer %s. '
                'Reset from printer menu: [3 SERWIS]/[3.3.1 ZEROWANIE]/[9 ZERUJ NOVIAPI]/[2 ODBLOKUJ]',
                printer.novitus_printer_ip
            )
            raise UserError(
                _('Token rate limit reached. Wait 1 hour or reset from printer menu:\n'
                  '[3 SERWIS] → [3.3.1 ZEROWANIE] → [9 ZERUJ NOVIAPI] → [2 ODBLOKUJ]')
            )

        if response.status_code != 200:
            raise UserError(
                _('Failed to acquire Novitus token. HTTP %s: %s') % (
                    response.status_code, response.text)
            )

        data = response.json()
        token = data.get('token', '')
        expiration_date = data.get('expiration_date', '')

        if not token:
            raise UserError(_('Novitus printer returned empty token.'))

        self._save_token(printer, token, expiration_date)
        return token

    def _refresh_token(self, printer):
        """PATCH /api/v1/token — use existing token in Authorization header.
        Does NOT count toward the 10-per-hour rate limit.
        """
        url = self._get_endpoint_url(printer, 'token')
        headers = self._get_headers(printer, include_auth=True)

        try:
            response = requests.patch(
                url, headers=headers, data='""',
                timeout=API_TIMEOUT_SECONDS
            )
        except requests.exceptions.RequestException as e:
            _logger.warning('Token refresh failed for %s, fetching new token: %s',
                            printer.novitus_printer_ip, str(e))
            return self._fetch_new_token(printer)

        if response.status_code == 429:
            _logger.critical(
                'Novitus token rate limit exceeded for printer %s.',
                printer.novitus_printer_ip
            )
            raise UserError(
                _('Token rate limit reached. Wait 1 hour or reset from printer menu:\n'
                  '[3 SERWIS] → [3.3.1 ZEROWANIE] → [9 ZERUJ NOVIAPI] → [2 ODBLOKUJ]')
            )

        if response.status_code not in (200, 201):
            _logger.warning('Token PATCH returned %s, fetching new token.', response.status_code)
            return self._fetch_new_token(printer)

        data = response.json()
        token = data.get('token', '')
        expiration_date = data.get('expiration_date', '')

        if not token:
            _logger.warning('Token PATCH returned empty token, fetching new.')
            return self._fetch_new_token(printer)

        self._save_token(printer, token, expiration_date)
        return token

    def _save_token(self, printer, token, expiration_date):
        """Cache token and expiry on the printer record."""
        vals = {'novitus_token_cache': token}

        if expiration_date:
            try:
                # NoviAPI returns ISO 8601: "2024-01-01T00:00:00Z"
                expiry_dt = datetime.fromisoformat(expiration_date.replace('Z', '+00:00'))
                vals['novitus_token_expiry'] = expiry_dt.replace(tzinfo=None)
            except (ValueError, AttributeError):
                _logger.warning('Could not parse token expiration_date: %s', expiration_date)
                # Default: expire in 20 minutes
                vals['novitus_token_expiry'] = fields.Datetime.now() + timedelta(minutes=20)
        else:
            vals['novitus_token_expiry'] = fields.Datetime.now() + timedelta(minutes=20)

        printer.sudo().write(vals)

    # ── HTTP client ───────────────────────────────────────────────────

    def _get_headers(self, printer, include_auth=True):
        """Build standard headers. include_auth=False for token endpoints."""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'NoviApi',
        }
        if include_auth:
            token = printer.novitus_token_cache
            if token:
                headers['Authorization'] = 'Bearer %s' % token
        return headers

    def _request(self, printer, method, url, json_body=None, include_auth=True):
        """
        Execute HTTP request with full error handling.
        Handles: 401 (auto-refresh + retry), 403 (retry with backoff),
        400/404/409/429/500/507 (raise UserError with clear message).
        Returns parsed JSON response dict.
        """
        max_retries_403 = printer.novitus_max_retries or 3
        attempt_401 = 0
        attempt_403 = 0

        while True:
            headers = self._get_headers(printer, include_auth=include_auth)

            try:
                if method == 'GET':
                    resp = requests.get(url, headers=headers, timeout=API_TIMEOUT_SECONDS)
                elif method == 'POST':
                    resp = requests.post(url, headers=headers, json=json_body, timeout=API_TIMEOUT_SECONDS)
                elif method == 'PUT':
                    resp = requests.put(url, headers=headers, data='""', timeout=API_TIMEOUT_SECONDS)
                elif method == 'PATCH':
                    resp = requests.patch(url, headers=headers, data='""', timeout=API_TIMEOUT_SECONDS)
                elif method == 'DELETE':
                    resp = requests.delete(url, headers=headers, timeout=API_TIMEOUT_SECONDS)
                else:
                    raise UserError(_('Unsupported HTTP method: %s') % method)
            except requests.exceptions.ConnectionError:
                raise UserError(
                    _('Cannot connect to Novitus printer at %s. '
                      'Check printer is on and network is connected.') % url
                )
            except requests.exceptions.Timeout:
                raise UserError(
                    _('Novitus printer at %s did not respond within %s seconds.') % (
                        url, API_TIMEOUT_SECONDS)
                )
            except requests.exceptions.RequestException as e:
                raise UserError(_('Novitus HTTP error: %s') % str(e))

            status = resp.status_code

            # Success
            if status in (200, 201):
                try:
                    return resp.json()
                except ValueError:
                    return {}

            # 401 — Token expired/invalid: auto-refresh once, retry
            if status == 401:
                attempt_401 += 1
                if attempt_401 > 1:
                    raise UserError(_('Authentication failed. Token refresh did not resolve the issue.'))
                _logger.info('Novitus 401 — refreshing token and retrying.')
                self._get_valid_token(printer)
                continue

            # 403 — Concurrency: another command is processing
            if status == 403:
                attempt_403 += 1
                if attempt_403 > max_retries_403:
                    raise UserError(
                        _('Printer busy (HTTP 403). Another command is still processing. '
                          'Retried %d times. Please wait and try again.') % max_retries_403
                    )
                _logger.info('Novitus 403 — concurrency, retry %d/%d',
                             attempt_403, max_retries_403)
                time.sleep(1)
                continue

            # 400 — JSON schema mismatch
            if status == 400:
                _logger.error('Novitus 400 — schema mismatch. Response: %s', resp.text)
                raise UserError(
                    _('Printer rejected the request (HTTP 400). '
                      'Payload format error:\n%s') % resp.text
                )

            # 404 — Job not found
            if status == 404:
                _logger.error('Novitus 404 — job not found. URL: %s', url)
                raise UserError(_('Print job not found (HTTP 404).'))

            # 409 — Daily report pending, all commands blocked
            if status == 409:
                raise UserError(
                    _('Daily Z-report is required before printing. '
                      'Please run the daily report first.')
                )

            # 429 — Token rate limit exceeded
            if status == 429:
                _logger.critical('Novitus 429 — token rate limit for %s', printer.novitus_printer_ip)
                raise UserError(
                    _('Token rate limit reached. Wait 1 hour or reset from printer menu:\n'
                      '[3 SERWIS] → [3.3.1 ZEROWANIE] → [9 ZERUJ NOVIAPI] → [2 ODBLOKUJ]')
                )

            # 500 — Internal printer error
            if status == 500:
                _logger.error('Novitus 500 — internal error. Response: %s', resp.text)
                raise UserError(
                    _('Printer internal error (HTTP 500):\n%s') % resp.text
                )

            # 507 — Protected memory full (fiscally critical)
            if status == 507:
                _logger.critical('Novitus 507 — protected memory full for %s',
                                 printer.novitus_printer_ip)
                raise UserError(
                    _('CRITICAL: Printer memory full. Fiscal receipts cannot be stored. '
                      'Contact system administrator immediately.')
                )

            # Unhandled status code
            _logger.error('Novitus unexpected HTTP %s. Response: %s', status, resp.text)
            raise UserError(
                _('Unexpected printer response (HTTP %s):\n%s') % (status, resp.text)
            )

    # ── 3-step command executor ───────────────────────────────────────

    def _execute_command(self, printer, endpoint_key, payload, poll_timeout_ms=None):
        """
        Execute any NoviAPI command using the 3-step flow:
          STEP A: POST → STORED (save id)
          STEP B: PUT /{id} → CONFIRMED
          STEP C: GET /{id}?timeout=N → poll until DONE or ERROR
        On exception between A and B: attempt DELETE /{id} to cancel.
        Returns: {'success': bool, 'status': str, 'jpkid': int,
                  'e_document': dict, 'error': str}
        """
        # Ensure we have a valid token
        self._get_valid_token(printer)

        base_url = self._get_endpoint_url(printer, endpoint_key)

        if poll_timeout_ms is None:
            poll_timeout_ms = printer.novitus_poll_timeout or DEFAULT_POLL_TIMEOUT_MS

        job_id = None

        # STEP A — Submit
        _logger.info('NoviAPI STEP A: POST %s', base_url)
        result_a = self._request(printer, 'POST', base_url, json_body=payload)

        request_data = result_a.get('request', {})
        job_id = request_data.get('id')
        step_a_status = request_data.get('status', '')

        if not job_id:
            return {
                'success': False,
                'status': step_a_status,
                'error': 'Printer did not return a job ID after POST. Response: %s' % str(result_a),
            }

        _logger.info('NoviAPI STEP A complete: job_id=%s, status=%s', job_id, step_a_status)

        # STEP B — Confirm
        confirm_url = '%s/%s' % (base_url, job_id)
        try:
            _logger.info('NoviAPI STEP B: PUT %s', confirm_url)
            result_b = self._request(printer, 'PUT', confirm_url)
            step_b_status = result_b.get('request', {}).get('status', '')
            _logger.info('NoviAPI STEP B complete: status=%s', step_b_status)
        except Exception as e:
            # Confirm failed — attempt to cancel the STORED job
            _logger.error('NoviAPI STEP B failed: %s. Attempting cancel.', str(e))
            self._cancel_job(printer, base_url, job_id)
            raise

        # STEP C — Poll for completion
        _logger.info('NoviAPI STEP C: polling %s/%s', base_url, job_id)
        return self._poll_status(printer, base_url, job_id, poll_timeout_ms)

    def _poll_status(self, printer, base_url, job_id, poll_timeout_ms):
        """Poll GET /{id}?timeout=N until DONE/ERROR or MAX_POLL_SECONDS elapsed."""
        poll_url = '%s/%s?timeout=%d' % (base_url, job_id, poll_timeout_ms)
        start_time = time.time()

        while True:
            elapsed = time.time() - start_time
            if elapsed >= MAX_POLL_SECONDS:
                _logger.error('NoviAPI polling timed out after %ds for job %s', MAX_POLL_SECONDS, job_id)
                raise UserError(
                    _('Printer did not respond in time (%d seconds). '
                      'Check printer status and retry.') % MAX_POLL_SECONDS
                )

            result = self._request(printer, 'GET', poll_url)
            request_data = result.get('request', {})
            status = request_data.get('status', '')

            if status == 'DONE':
                _logger.info('NoviAPI command DONE: job_id=%s, jpkid=%s',
                             job_id, request_data.get('jpkid'))
                return {
                    'success': True,
                    'status': 'DONE',
                    'jpkid': request_data.get('jpkid', 0),
                    'e_document': request_data.get('e_document', {}),
                    'error': '',
                }

            if status == 'ERROR':
                error_msg = request_data.get('error', str(result))
                _logger.error('NoviAPI command ERROR: job_id=%s, error=%s', job_id, error_msg)
                return {
                    'success': False,
                    'status': 'ERROR',
                    'jpkid': 0,
                    'e_document': {},
                    'error': error_msg,
                }

            # Still processing (CONFIRMED, QUEUED, etc.) — continue polling
            _logger.debug('NoviAPI poll status=%s, elapsed=%.1fs', status, elapsed)

    def _cancel_job(self, printer, base_url, job_id):
        """Attempt to cancel a STORED/QUEUED job via DELETE. Best effort."""
        cancel_url = '%s/%s' % (base_url, job_id)
        try:
            _logger.info('NoviAPI CANCEL: DELETE %s', cancel_url)
            self._request(printer, 'DELETE', cancel_url)
            _logger.info('NoviAPI job %s cancelled successfully.', job_id)
        except Exception as e:
            _logger.warning('NoviAPI cancel failed for job %s: %s (may already be processed)',
                            job_id, str(e))

    # ── Fiscal calculations ───────────────────────────────────────────

    @staticmethod
    def _calculate_gross(unit_price, quantity):
        """
        Calculate gross value using Decimal arithmetic.
        round(unit_price * quantity, 2) — uses ROUND_HALF_UP.
        This MUST match what the printer calculates or error 20 occurs.
        """
        d_price = Decimal(str(unit_price))
        d_qty = Decimal(str(quantity))
        gross = (d_price * d_qty).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return gross

    @staticmethod
    def _get_ptu_char(tax_amount):
        """
        Map Odoo tax amount (percentage) to PTU character.
        A=23%, B=8%, C=5%, D=0%, E=exempt, Z=free-rated.
        """
        if tax_amount == 23:
            return 'A'
        elif tax_amount == 8:
            return 'B'
        elif tax_amount == 5:
            return 'C'
        elif tax_amount == 0:
            return 'D'
        else:
            return 'E'

    def _get_ptu_for_line(self, line, printer):
        """
        Map order line taxes to PTU character using printer PTU mappings first,
        then fall back to amount-based matching.
        """
        taxes = line.tax_ids_after_fiscal_position
        if not taxes:
            return 'D'

        tax = taxes[0]

        # Check explicit PTU mappings on printer
        if tax == printer.novitus_ptu_a_tax_id:
            return 'A'
        elif tax == printer.novitus_ptu_b_tax_id:
            return 'B'
        elif tax == printer.novitus_ptu_c_tax_id:
            return 'C'
        elif tax == printer.novitus_ptu_d_tax_id:
            return 'D'
        elif tax == printer.novitus_ptu_e_tax_id:
            return 'E'

        # Fallback: map by tax amount
        return self._get_ptu_char(tax.amount)

    def _map_payment_type(self, payment_method):
        """
        Map Odoo payment method to NoviAPI payment type integer.
        0=cash, 1=card, 2=cheque, 3=voucher, 4=other, 5=credit, 8=transfer
        """
        if not payment_method:
            return PAYMENT_TYPE_CASH

        pm_type = payment_method.type
        if pm_type == 'cash':
            return PAYMENT_TYPE_CASH
        elif pm_type == 'bank':
            return PAYMENT_TYPE_CARD
        elif pm_type == 'pay_later':
            return PAYMENT_TYPE_CREDIT
        else:
            return PAYMENT_TYPE_OTHER

    # ── Receipt building ──────────────────────────────────────────────

    def _build_receipt_direct_io(self, order, printer):
        """
        Build direct_io payload for a fiscal receipt.
        Uses serial protocol commands: $h → $l (×N) → $b (×M) → $y
        Returns: {"direct_io": {"nov_cmd": {...}}}

        Command structure follows the Novitus serial protocol PDF.
        """
        # $h — Begin transaction
        cashier = printer.novitus_cashier_id or order.user_id.name or 'ODOO'

        # $l — Line items
        items = []
        for line in order.lines:
            if line.display_type in ('line_section', 'line_note'):
                continue

            ptu = self._get_ptu_for_line(line, printer)
            unit_price = Decimal(str(line.price_unit))
            qty = Decimal(str(line.qty))
            gross_value = self._calculate_gross(line.price_unit, line.qty)

            # Product name: max 40 chars per Novitus protocol
            product_name = (line.product_id.name or line.full_product_name or 'Product')[:40]

            items.append({
                'name': product_name,
                'quantity': str(qty),
                'unit_price': str(unit_price),
                'gross_value': str(gross_value),
                'ptu': ptu,
            })

        # $b — Payment forms
        payments = []
        for payment in order.payment_ids:
            pay_type = self._map_payment_type(payment.payment_method_id)
            pay_amount = Decimal(str(payment.amount)).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
            payments.append({
                'type': pay_type,
                'value': str(pay_amount),
            })

        # If no payments recorded, default to cash for the total
        if not payments:
            total = Decimal(str(order.amount_total)).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
            payments.append({
                'type': PAYMENT_TYPE_CASH,
                'value': str(total),
            })

        # Build the full direct_io payload
        # Buyer NIP for B2B (faktura do paragonu) — 10 digits, no hyphens
        buyer_nip = ''
        if order.partner_id and order.partner_id.vat:
            buyer_nip = order.partner_id.vat.replace('-', '').replace(' ', '')
            # Strip country prefix if present (PL)
            if buyer_nip.upper().startswith('PL'):
                buyer_nip = buyer_nip[2:]

        # $y — Close transaction
        total_gross = Decimal(str(order.amount_total)).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )

        payload = {
            'direct_io': {
                'nov_cmd': {
                    'h': {
                        'cashier': cashier,
                        'system_no': order.pos_reference or order.name,
                    },
                    'l': items,
                    'b': payments,
                    'y': {
                        'total': str(total_gross),
                        'buyer_nip': buyer_nip,
                    },
                }
            }
        }

        return payload

    # ── Public API methods ────────────────────────────────────────────

    @api.model
    def test_connection(self, printer):
        """
        GET /api/v1 — connection test from backend (pos.printer button).
        Returns dict with success/error/elapsed for the printer form view.
        """
        t0 = time.time()
        try:
            url = self._get_endpoint_url(printer, 'test')
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'NoviApi',
            }

            response = requests.get(url, headers=headers, timeout=CONNECT_TEST_TIMEOUT_SECONDS)

            elapsed = round(time.time() - t0, 2)
            if response.status_code == 200:
                try:
                    data = response.json()
                except ValueError:
                    data = {}
                return {
                    'success': True,
                    'elapsed': elapsed,
                    'message': _('Connected successfully'),
                    'printer_info': {
                        'model': data.get('model', data.get('printerModel', 'Unknown')),
                        'fiscal_id': data.get('fiscalId', data.get('nip',
                                     data.get('serialNumber', 'Unknown'))),
                    }
                }
            else:
                return {
                    'success': False,
                    'elapsed': elapsed,
                    'error': 'HTTP %s: %s' % (response.status_code, response.text),
                }
        except requests.exceptions.RequestException as e:
            elapsed = round(time.time() - t0, 2)
            return {
                'success': False,
                'elapsed': elapsed,
                'error': str(e),
            }

    @api.model
    def test_connection_from_pos(self, printer_id):
        """
        GET /api/v1 — connection test from POS frontend.
        Returns True on 200 OK, False on any error.
        Does NOT raise — returns bool for JS to handle.
        Uses short timeout (5s) so UI stays responsive.
        """
        printer = self.env['pos.printer'].browse(printer_id)
        if not printer.exists():
            return False

        try:
            url = self._get_endpoint_url(printer, 'test')
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'NoviApi',
            }
            response = requests.get(url, headers=headers, timeout=CONNECT_TEST_TIMEOUT_SECONDS)
            return response.status_code == 200
        except Exception:
            return False

    @api.model
    def print_fiscal_receipt_from_pos(self, order_name, printer_id):
        """
        Build and send a fiscal receipt for the given order.
        Uses direct_io as primary path.
        Returns result dict for JS to store fiscal data.
        """
        printer = self.env['pos.printer'].browse(printer_id)
        if not printer.exists():
            return {'success': False, 'error': 'Printer not found'}

        # Find the order by name/reference
        order = self.env['pos.order'].search([
            '|',
            ('name', '=', order_name),
            ('pos_reference', '=', order_name),
        ], limit=1)

        if not order:
            return {'success': False, 'error': 'Order %s not found' % order_name}

        # Check if already fiscalized
        if order.is_fiscal_receipt and order.fiscal_receipt_number:
            return {
                'success': True,
                'fiscal_number': order.fiscal_receipt_number,
                'printer_id': order.fiscal_printer_id,
                'jpkid': 0,
                'already_printed': True,
            }

        # Build direct_io payload
        payload = self._build_receipt_direct_io(order, printer)

        # Execute 3-step command flow
        _logger.info('Printing fiscal receipt for order %s via direct_io', order_name)
        result = self._execute_command(printer, 'direct_io', payload)

        if result.get('success'):
            # Extract fiscal number from e_document or jpkid
            e_doc = result.get('e_document', {})
            fiscal_number = (
                e_doc.get('fiscal_number') or
                e_doc.get('receipt_number') or
                str(result.get('jpkid', ''))
            )

            # Update order with fiscal data
            order.sudo().write({
                'is_fiscal_receipt': True,
                'fiscal_receipt_number': fiscal_number,
                'fiscal_printer_id': printer.novitus_fiscal_id or printer.novitus_printer_ip,
                'fiscal_receipt_date': fields.Datetime.now(),
                'fiscal_print_status': 'printed',
                'fiscal_print_error': False,
                'crk_transmitted': True,
                'crk_transmission_date': fields.Datetime.now(),
            })

            return {
                'success': True,
                'fiscal_number': fiscal_number,
                'printer_id': printer.novitus_fiscal_id or printer.novitus_printer_ip,
                'jpkid': result.get('jpkid', 0),
                'crk_transmitted': True,
            }
        else:
            # Update order with error
            order.sudo().write({
                'fiscal_print_status': 'failed',
                'fiscal_print_error': result.get('error', 'Unknown error'),
                'fiscal_retry_count': order.fiscal_retry_count + 1,
            })

            return {
                'success': False,
                'error': result.get('error', 'Unknown error'),
            }

    @api.model
    def print_daily_report_from_pos(self, printer_id):
        """
        Check queue, then send daily Z-report.
        Raises UserError if queue is not empty.
        """
        printer = self.env['pos.printer'].browse(printer_id)
        if not printer.exists():
            return {'success': False, 'error': 'Printer not found'}

        # Check queue first
        queue_count = self.get_queue_status(printer_id)
        if queue_count > 0:
            raise UserError(
                _('Queue has %d pending jobs. Clear the queue before running daily report.') % queue_count
            )

        # Build daily report payload
        today = fields.Date.today()
        payload = {
            'daily_report': {
                'date': today.strftime('%d/%m/%Y'),
                'system_info': {},
            }
        }

        _logger.info('Sending daily Z-report for %s', today.strftime('%d/%m/%Y'))
        result = self._execute_command(printer, 'daily_report', payload)

        return result

    @api.model
    def open_cashbox(self, printer_id):
        """
        Open cash drawer via direct_io.
        Uses the $d serial command for drawer open.
        """
        printer = self.env['pos.printer'].browse(printer_id)
        if not printer.exists():
            return False

        payload = {
            'direct_io': {
                'nov_cmd': {
                    'd': {},
                }
            }
        }

        try:
            result = self._execute_command(printer, 'direct_io', payload)
            return result.get('success', False)
        except Exception as e:
            _logger.error('Failed to open cash drawer: %s', str(e))
            return False

    @api.model
    def get_queue_status(self, printer_id):
        """GET /api/v1/queue → requests_in_queue count."""
        printer = self.env['pos.printer'].browse(printer_id)
        if not printer.exists():
            return 0

        self._get_valid_token(printer)
        url = self._get_endpoint_url(printer, 'queue')

        try:
            result = self._request(printer, 'GET', url)
            return result.get('requests_in_queue', 0)
        except Exception as e:
            _logger.error('Failed to get queue status: %s', str(e))
            return 0

    @api.model
    def clear_queue(self, printer_id):
        """DELETE /api/v1/queue → clear pending jobs."""
        printer = self.env['pos.printer'].browse(printer_id)
        if not printer.exists():
            return False

        self._get_valid_token(printer)
        url = self._get_endpoint_url(printer, 'queue')

        try:
            self._request(printer, 'DELETE', url)
            _logger.info('Queue cleared for printer %s', printer.novitus_printer_ip)
            return True
        except Exception as e:
            _logger.error('Failed to clear queue: %s', str(e))
            return False

    def action_print_fiscal_receipt(self):
        """
        Backend retry action called from pos.order form view retry button.
        self = pos.order recordset (single record) — called via button on pos.order.
        Note: This method is called in the context of novitus.noviapi but receives
        the order through the calling context.
        """
        # This is called from pos.order, so we need to get printer from the order's session
        order = self.env.context.get('active_id') and self.env['pos.order'].browse(
            self.env.context['active_id']
        )
        if not order or not order.exists():
            raise UserError(_('No order found.'))

        if order.is_fiscal_receipt and order.fiscal_receipt_number:
            raise UserError(
                _('This order already has a fiscal receipt.\n'
                  'Fiscal Number: %s\nPrinted: %s') % (
                    order.fiscal_receipt_number,
                    order.fiscal_receipt_date
                )
            )

        # Get Novitus printer from POS config
        printer = order.session_id.config_id.printer_ids.filtered(
            lambda p: p.printer_type == 'novitus_online'
        )[:1]

        if not printer:
            raise UserError(
                _('No Novitus fiscal printer configured for this POS.\n'
                  'Please configure a Novitus printer in POS settings.')
            )

        if order.fiscal_retry_count >= (printer.novitus_max_retries or 3):
            raise UserError(
                _('Maximum retry attempts reached (%d).\n'
                  'Please check printer and try again later.') % (printer.novitus_max_retries or 3)
            )

        # Build and send
        order.write({'fiscal_print_status': 'printing'})
        payload = self._build_receipt_direct_io(order, printer)

        try:
            result = self._execute_command(printer, 'direct_io', payload)

            if result.get('success'):
                e_doc = result.get('e_document', {})
                fiscal_number = (
                    e_doc.get('fiscal_number') or
                    e_doc.get('receipt_number') or
                    str(result.get('jpkid', ''))
                )

                order.write({
                    'is_fiscal_receipt': True,
                    'fiscal_receipt_number': fiscal_number,
                    'fiscal_printer_id': printer.novitus_fiscal_id or printer.novitus_printer_ip,
                    'fiscal_receipt_date': fields.Datetime.now(),
                    'fiscal_print_status': 'printed',
                    'fiscal_print_error': False,
                    'crk_transmitted': True,
                    'crk_transmission_date': fields.Datetime.now(),
                })

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Fiscal Receipt Printed'),
                        'message': _('Fiscal Number: %s (JPK: %s)') % (
                            fiscal_number, result.get('jpkid', '')),
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                order.write({
                    'fiscal_print_status': 'failed',
                    'fiscal_print_error': result.get('error', 'Unknown error'),
                    'fiscal_retry_count': order.fiscal_retry_count + 1,
                })
                raise UserError(
                    _('Fiscal receipt printing failed.\nError: %s') % result.get('error')
                )
        except UserError:
            raise
        except Exception as e:
            order.write({
                'fiscal_print_status': 'failed',
                'fiscal_print_error': str(e),
                'fiscal_retry_count': order.fiscal_retry_count + 1,
            })
            raise UserError(_('Fiscal receipt printing failed.\nError: %s') % str(e))
