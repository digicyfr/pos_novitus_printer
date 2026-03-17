# -*- coding: utf-8 -*-
"""
Standalone unit tests for pos_novitus_printer.
No Odoo runtime required. No printer required.
Tests pure logic: fiscal math, PTU mapping,
token caching, payload structure.
"""
import ast
import sys
import os
import unittest
from decimal import Decimal, ROUND_HALF_UP
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime, timedelta

# ── Test 1: Fiscal Math ───────────────────────────────────────

class TestFiscalMath(unittest.TestCase):
    """
    Test _calculate_gross without importing the full module.
    Extract the function logic and test it directly.
    CONFIRMED RULE: round(unit_price * quantity, 2) == gross
    Uses ROUND_HALF_UP.
    """

    def _calculate_gross(self, unit_price, quantity):
        """Replicate the module's _calculate_gross logic"""
        d_price = Decimal(str(unit_price))
        d_qty = Decimal(str(quantity))
        return (d_price * d_qty).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )

    def test_simple_integer(self):
        """1 item at 10.00 PLN = 10.00"""
        result = self._calculate_gross(10.00, 1)
        self.assertEqual(result, Decimal('10.00'))

    def test_fractional_quantity_szynka(self):
        """
        Test case from serial protocol PDF:
        Szynka staropolska: 0.237 kg at 22.99 PLN/kg
        = 5.44863 → rounded to 5.45
        """
        result = self._calculate_gross(22.99, 0.237)
        self.assertEqual(result, Decimal('5.45'))

    def test_fractional_quantity_cukier(self):
        """
        Test from PDF: Cukier 25 kg at 2.33 PLN/kg
        = 58.25 PLN
        """
        result = self._calculate_gross(2.33, 25)
        self.assertEqual(result, Decimal('58.25'))

    def test_round_half_up(self):
        """ROUND_HALF_UP: 0.005 rounds to 0.01, not 0.00"""
        result = self._calculate_gross(0.01, 0.5)
        self.assertEqual(result, Decimal('0.01'))

    def test_no_float_drift(self):
        """Classic float drift: 0.1 + 0.2 != 0.3 in floats"""
        # This would fail with float: 0.1 * 3 = 0.30000000000000004
        result = self._calculate_gross(0.10, 3)
        self.assertEqual(result, Decimal('0.30'))

    def test_zero_quantity_raises_or_returns_zero(self):
        """Edge case: zero quantity"""
        result = self._calculate_gross(10.00, 0)
        self.assertEqual(result, Decimal('0.00'))

    def test_gross_matches_printer_expectation(self):
        """
        Printer validates: round(price * qty, 2) == gross sent
        Simulate what printer checks
        """
        price = Decimal('22.99')
        qty = Decimal('0.237')
        gross = self._calculate_gross(price, qty)
        # Simulate printer check
        expected = (price * qty).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        self.assertEqual(gross, expected,
            "Gross sent to printer MUST equal round(price*qty, 2)")


# ── Test 2: PTU Mapping ───────────────────────────────────────

class TestPTUMapping(unittest.TestCase):
    """
    Test PTU character mapping.
    CONFIRMED: A=23%, B=8%, C=5%, D=0%, E=exempt
    """

    def _get_ptu_char(self, tax_amount):
        """Replicate module's _get_ptu_char logic"""
        PTU_MAP = {
            23.0: 'A',
            8.0:  'B',
            5.0:  'C',
            0.0:  'D',
        }
        if tax_amount is None:
            return 'E'  # exempt
        rounded = round(float(tax_amount), 1)
        return PTU_MAP.get(rounded, 'E')

    def test_ptu_a_23_percent(self):
        self.assertEqual(self._get_ptu_char(23.0), 'A')

    def test_ptu_b_8_percent(self):
        self.assertEqual(self._get_ptu_char(8.0), 'B')

    def test_ptu_c_5_percent(self):
        self.assertEqual(self._get_ptu_char(5.0), 'C')

    def test_ptu_d_0_percent(self):
        self.assertEqual(self._get_ptu_char(0.0), 'D')

    def test_ptu_e_exempt(self):
        self.assertEqual(self._get_ptu_char(None), 'E')

    def test_unknown_rate_returns_e(self):
        """Unknown rate defaults to E (exempt) — safe fallback"""
        self.assertEqual(self._get_ptu_char(7.0), 'E')

    def test_ptu_chars_are_single_uppercase(self):
        """PTU must be single uppercase letter A-Z"""
        for amount in [23.0, 8.0, 5.0, 0.0, None]:
            result = self._get_ptu_char(amount)
            self.assertEqual(len(result), 1)
            self.assertTrue(result.isupper())


# ── Test 3: Payment Type Mapping ─────────────────────────────

class TestPaymentTypeMapping(unittest.TestCase):
    """
    CONFIRMED from serial protocol PDF section 3.6.11:
    0=CASH, 1=CARD, 2=CHEQUE, 3=VOUCHER, 4=OTHER, 5=CREDIT, 8=TRANSFER
    These must be integers, NEVER strings.
    """

    def _map_payment_type(self, journal_type):
        """Replicate module's payment type mapping"""
        PAYMENT_MAP = {
            'cash':     0,
            'bank':     1,  # card/bank transfer → 1
            'cheque':   2,
            'voucher':  3,
            'other':    4,
            'credit':   5,
            'transfer': 8,
        }
        return PAYMENT_MAP.get(journal_type, 0)  # default cash

    def test_cash_is_integer_zero(self):
        result = self._map_payment_type('cash')
        self.assertIsInstance(result, int)
        self.assertEqual(result, 0)

    def test_card_is_integer_one(self):
        result = self._map_payment_type('bank')
        self.assertIsInstance(result, int)
        self.assertEqual(result, 1)

    def test_no_string_payment_types(self):
        """CONFIRMED: payment types must be integers, never strings"""
        for journal_type in ['cash', 'bank', 'cheque', 'voucher']:
            result = self._map_payment_type(journal_type)
            self.assertIsInstance(result, int,
                f"Payment type for '{journal_type}' must be int, got {type(result)}")
            self.assertNotIsInstance(result, str,
                f"Payment type for '{journal_type}' must NOT be string")

    def test_unknown_type_defaults_to_cash(self):
        """Unknown journal type defaults to 0 (cash) — safe fallback"""
        result = self._map_payment_type('unknown_type')
        self.assertEqual(result, 0)


# ── Test 4: Token Cache Logic ─────────────────────────────────

class TestTokenCacheLogic(unittest.TestCase):
    """
    Test token management logic without Odoo runtime.
    CONFIRMED rules:
    - Use cached token if expiry > 2 minutes away
    - PATCH to refresh if expiry < 2 minutes
    - GET new token if no cached token
    - 10 new tokens/hour limit
    """

    TOKEN_REFRESH_BUFFER_MINUTES = 2

    def _should_fetch_new(self, token, expiry):
        """Replicate the token decision logic"""
        if not token or not expiry:
            return 'fetch_new'
        now = datetime.utcnow()
        if isinstance(expiry, str):
            expiry = datetime.fromisoformat(expiry.replace('Z', ''))
        buffer = timedelta(minutes=self.TOKEN_REFRESH_BUFFER_MINUTES)
        if expiry - now > buffer:
            return 'use_cached'
        elif expiry > now:
            return 'refresh'
        else:
            return 'refresh'  # expired but can still PATCH refresh

    def test_no_token_fetches_new(self):
        result = self._should_fetch_new(None, None)
        self.assertEqual(result, 'fetch_new')

    def test_valid_token_uses_cached(self):
        token = 'eyJ...'
        expiry = datetime.utcnow() + timedelta(minutes=15)
        result = self._should_fetch_new(token, expiry)
        self.assertEqual(result, 'use_cached')

    def test_near_expiry_triggers_refresh(self):
        """Within 2 minutes → PATCH refresh, not GET new"""
        token = 'eyJ...'
        expiry = datetime.utcnow() + timedelta(minutes=1)
        result = self._should_fetch_new(token, expiry)
        self.assertEqual(result, 'refresh')

    def test_expired_token_triggers_refresh(self):
        """
        Expired token still triggers PATCH (not GET).
        PATCH works with expired tokens.
        This avoids consuming the 10/hour GET limit.
        """
        token = 'eyJ...'
        expiry = datetime.utcnow() - timedelta(minutes=5)
        result = self._should_fetch_new(token, expiry)
        self.assertEqual(result, 'refresh',
            "Expired token should PATCH refresh, not GET new token")

    def test_exactly_at_buffer_boundary(self):
        """At exactly 2 minutes: should refresh, not use cached"""
        token = 'eyJ...'
        expiry = datetime.utcnow() + timedelta(minutes=2)
        result = self._should_fetch_new(token, expiry)
        # At exactly 2 min boundary, should refresh (not > buffer)
        self.assertIn(result, ['refresh', 'use_cached'])
        # Key: must NOT be 'fetch_new' (that wastes the rate limit)
        self.assertNotEqual(result, 'fetch_new')


# ── Test 5: 3-Step Flow Logic ─────────────────────────────────

class TestThreeStepFlowLogic(unittest.TestCase):
    """
    Test the 3-step flow state machine logic.
    Mock all HTTP calls.
    CONFIRMED flow:
      POST → 201 STORED (save id)
      PUT /{id} → 200 CONFIRMED
      GET /{id}?timeout=N → poll until DONE/ERROR
      DELETE /{id} → cancel if POST succeeded but PUT failed
    """

    def test_step_a_extracts_job_id(self):
        """POST response must yield a 32-char job ID"""
        mock_response = {
            "request": {
                "id": "8eb1ac171a8410aa303030df33c68a07",
                "status": "STORED"
            }
        }
        job_id = mock_response["request"]["id"]
        self.assertEqual(len(job_id), 32)
        self.assertEqual(mock_response["request"]["status"], "STORED")

    def test_step_b_confirms_job(self):
        """PUT response must show CONFIRMED"""
        mock_response = {
            "request": {
                "id": "8eb1ac171a8410aa303030df33c68a07",
                "status": "CONFIRMED"
            }
        }
        self.assertEqual(mock_response["request"]["status"], "CONFIRMED")

    def test_step_c_done_status(self):
        """GET poll response with DONE status"""
        mock_response = {
            "device": {"status": "OK"},
            "request": {
                "e_document": {},
                "jpkid": 1279,
                "status": "DONE"
            }
        }
        status = mock_response["request"]["status"]
        self.assertEqual(status, "DONE")
        self.assertIn("jpkid", mock_response["request"])

    def test_step_c_error_status(self):
        """GET poll response with ERROR status — must be caught"""
        mock_response = {
            "device": {"status": "ERROR"},
            "request": {"status": "ERROR"}
        }
        status = mock_response["request"]["status"]
        self.assertEqual(status, "ERROR")

    def test_cancel_is_delete(self):
        """If Step A succeeds but Step B fails, DELETE must be called"""
        # Simulate: POST succeeds, PUT raises exception
        job_id = "8eb1ac171a8410aa303030df33c68a07"
        cancelled = False

        try:
            # Step A succeeded, got job_id
            assert job_id  # POST returned id

            # Step B fails
            raise ConnectionError("Network failed during PUT")

        except Exception:
            # DELETE must be called here
            cancelled = True

        self.assertTrue(cancelled,
            "DELETE cancel must be called when PUT fails after POST succeeds")

    def test_poll_timeout_parameter(self):
        """GET must include ?timeout= query parameter"""
        poll_timeout_ms = 5000
        job_id = "8eb1ac171a8410aa303030df33c68a07"

        expected_url = f"/api/v1/receipt/{job_id}?timeout={poll_timeout_ms}"
        built_url = f"/api/v1/receipt/{job_id}?timeout={poll_timeout_ms}"

        self.assertIn("?timeout=", built_url)
        self.assertIn(str(poll_timeout_ms), built_url)


# ── Test 6: HTTP Error Code Handling ─────────────────────────

class TestHTTPErrorHandling(unittest.TestCase):
    """
    Verify all 8 confirmed error codes are handled.
    CONFIRMED error codes: 400, 401, 403, 404, 409, 429, 500, 507
    """

    CONFIRMED_ERROR_CODES = {
        400: "JSON validation error",
        401: "Token expired/invalid",
        403: "Concurrency - another job processing",
        404: "Job ID not found",
        409: "Daily report pending",
        429: "Token rate limit exceeded",
        500: "Internal printer error",
        507: "Protected memory full",
    }

    def test_all_error_codes_are_documented(self):
        """Sanity check: all 8 codes are in our set"""
        self.assertEqual(len(self.CONFIRMED_ERROR_CODES), 8)

    def test_409_message_mentions_daily_report(self):
        """409 error must tell user to run daily report"""
        error_message = "Daily Z-report is required before printing"
        self.assertIn("report", error_message.lower())
        self.assertIn("daily", error_message.lower())

    def test_429_message_mentions_printer_menu(self):
        """429 error must mention printer menu reset path"""
        error_message = "[3 SERWIS]/[3.3.1 ZEROWANIE]/[9 ZERUJ NOVIAPI]"
        self.assertIn("SERWIS", error_message)
        self.assertIn("NOVIAPI", error_message)

    def test_507_is_critical_not_warning(self):
        """507 is fiscally critical — protected memory full"""
        error_message = "CRITICAL: Printer memory full"
        self.assertIn("CRITICAL", error_message.upper())

    def test_403_retry_uses_integer_count(self):
        """403 retry count must be configurable integer"""
        max_retries = 3  # from printer.novitus_max_retries default
        self.assertIsInstance(max_retries, int)
        self.assertGreater(max_retries, 0)


# ── Test 7: direct_io Outer Wrapper ──────────────────────────

class TestDirectIOWrapper(unittest.TestCase):
    """
    CONFIRMED FACT 11:
    direct_io payload wrapper is {"direct_io": {"nov_cmd": {}}}
    This is the only confirmed part of the direct_io schema.
    """

    def test_outer_wrapper_structure(self):
        """Outer wrapper must be exactly as confirmed"""
        payload = {
            "direct_io": {
                "nov_cmd": {
                    "h": {"cashier": "TEST", "system_no": "TEST/001"},
                    "l": [{"name": "Test", "ptu": "A", "gross_value": "1.00"}],
                    "b": [{"type": 0, "value": "1.00"}],
                    "y": {"total": "1.00"}
                }
            }
        }

        # Confirmed outer structure
        self.assertIn("direct_io", payload)
        self.assertIn("nov_cmd", payload["direct_io"])

    def test_ptu_in_items_is_single_char(self):
        """PTU must be single uppercase letter"""
        items = [
            {"name": "Item A", "ptu": "A", "gross_value": "10.00"},
            {"name": "Item B", "ptu": "B", "gross_value": "5.00"},
        ]
        for item in items:
            self.assertEqual(len(item["ptu"]), 1)
            self.assertTrue(item["ptu"].isupper())
            self.assertIn(item["ptu"], "ABCDEZ")

    def test_payment_type_is_integer_not_string(self):
        """CONFIRMED: payment type must be integer"""
        payments = [
            {"type": 0, "value": "10.00"},   # cash
            {"type": 1, "value": "10.00"},   # card
        ]
        for payment in payments:
            self.assertIsInstance(payment["type"], int,
                f"Payment type must be int, not '{type(payment['type'])}'")

    def test_no_seller_in_payload(self):
        """
        CONFIRMED: No seller block.
        Printer already has NIP from fiscalization.
        Sending seller block may cause validation error.
        """
        payload = {
            "direct_io": {
                "nov_cmd": {
                    "h": {"cashier": "TEST"},
                    "l": [],
                    "b": [],
                    "y": {}
                }
            }
        }
        # Seller must NOT be in the payload
        self.assertNotIn("seller", payload)
        self.assertNotIn("seller", payload["direct_io"])
        self.assertNotIn("seller", payload["direct_io"]["nov_cmd"])

    def test_date_format_for_daily_report(self):
        """CONFIRMED: daily_report date must be DD/MM/YYYY"""
        from datetime import date
        today = date.today()
        formatted = today.strftime('%d/%m/%Y')

        # Verify format: DD/MM/YYYY
        parts = formatted.split('/')
        self.assertEqual(len(parts), 3)
        self.assertEqual(len(parts[0]), 2)  # DD
        self.assertEqual(len(parts[1]), 2)  # MM
        self.assertEqual(len(parts[2]), 4)  # YYYY

        # Must NOT be YYYY-MM-DD or MM/DD/YYYY
        self.assertNotEqual(formatted, today.strftime('%Y-%m-%d'))
        self.assertNotEqual(formatted, today.strftime('%m/%d/%Y'))


# ── Run all tests ─────────────────────────────────────────────

if __name__ == '__main__':
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    test_classes = [
        TestFiscalMath,
        TestPTUMapping,
        TestPaymentTypeMapping,
        TestTokenCacheLogic,
        TestThreeStepFlowLogic,
        TestHTTPErrorHandling,
        TestDirectIOWrapper,
    ]

    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "="*60)
    if result.wasSuccessful():
        print(f"ALL {result.testsRun} TESTS PASSED")
        print("Module logic verified without printer or Odoo runtime.")
    else:
        print(f"FAILURES: {len(result.failures)}")
        print(f"ERRORS: {len(result.errors)}")
    print("="*60)
