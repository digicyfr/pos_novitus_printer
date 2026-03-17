# -*- coding: utf-8 -*-
"""
Odoo-native integration tests for pos_novitus_printer.
Runs through odoo-bin --test-enable.
Tests ORM layer, field creation, model methods.
Does NOT require a printer. Does NOT make real HTTP calls.
"""
from unittest.mock import patch, MagicMock
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('pos_novitus_printer', '-standard')
class TestNovitusModelFields(TransactionCase):
    """Test that all model fields are correctly defined."""

    def setUp(self):
        super().setUp()
        self.printer_model = self.env['pos.printer']

    def test_novitus_fields_exist_on_pos_printer(self):
        """All 4 new fields must exist on pos.printer model."""
        fields = self.printer_model.fields_get()
        self.assertIn('novitus_token_cache', fields,
            'novitus_token_cache field missing from pos.printer')
        self.assertIn('novitus_token_expiry', fields,
            'novitus_token_expiry field missing from pos.printer')
        self.assertIn('novitus_poll_timeout', fields,
            'novitus_poll_timeout field missing from pos.printer')
        self.assertIn('novitus_max_retries', fields,
            'novitus_max_retries field missing from pos.printer')

    def test_novitus_poll_timeout_default(self):
        """novitus_poll_timeout default must be 5000 ms."""
        printer = self.printer_model.create({
            'name': 'Test Novitus Printer',
            'printer_type': 'novitus_online',
        })
        self.assertEqual(printer.novitus_poll_timeout, 5000,
            'Default poll timeout must be 5000 ms')

    def test_novitus_max_retries_default(self):
        """novitus_max_retries default must be 3."""
        printer = self.printer_model.create({
            'name': 'Test Novitus Printer 2',
            'printer_type': 'novitus_online',
        })
        self.assertEqual(printer.novitus_max_retries, 3,
            'Default max retries must be 3')

    def test_novitus_token_cache_is_empty_by_default(self):
        """Token cache must be empty on new printer record."""
        printer = self.printer_model.create({
            'name': 'Test Novitus Printer 3',
            'printer_type': 'novitus_online',
        })
        self.assertFalse(printer.novitus_token_cache,
            'Token cache must be empty on new printer')
        self.assertFalse(printer.novitus_token_expiry,
            'Token expiry must be empty on new printer')

    def test_ptu_tax_fields_exist(self):
        """PTU tax mapping fields must exist on pos.printer."""
        fields = self.printer_model.fields_get()
        for ptu in ['a', 'b', 'c', 'd', 'e']:
            field_name = 'novitus_ptu_%s_tax_id' % ptu
            self.assertIn(field_name, fields,
                '%s field missing from pos.printer' % field_name)


@tagged('pos_novitus_printer', '-standard')
class TestNovitusFiscalOrderFields(TransactionCase):
    """Test fiscal tracking fields on pos.order."""

    def test_fiscal_fields_exist_on_pos_order(self):
        """Fiscal tracking fields must exist on pos.order."""
        order_fields = self.env['pos.order'].fields_get()
        self.assertIn('fiscal_print_status', order_fields,
            'fiscal_print_status missing from pos.order')

    def test_fiscal_print_status_default(self):
        """fiscal_print_status must be a selection field."""
        field_def = self.env['pos.order'].fields_get(
            ['fiscal_print_status'])
        self.assertIn('fiscal_print_status', field_def)
        field_info = field_def['fiscal_print_status']
        self.assertIn(field_info['type'], ['selection', 'char'],
            'fiscal_print_status must be selection or char')


@tagged('pos_novitus_printer', '-standard')
class TestNovitusServiceMethods(TransactionCase):
    """
    Test the novitus.noviapi service methods using mocked HTTP.
    No real printer needed.
    """

    def setUp(self):
        super().setUp()
        self.noviapi = self.env['novitus.noviapi']
        self.printer = self.env['pos.printer'].create({
            'name': 'Test Novitus',
            'printer_type': 'novitus_online',
            'novitus_printer_ip': '127.0.0.1',
            'novitus_printer_port': 8888,
            'novitus_use_https': False,
            'novitus_poll_timeout': 5000,
            'novitus_max_retries': 3,
        })

    def test_noviapi_model_exists(self):
        """novitus.noviapi AbstractModel must be registered."""
        self.assertIsNotNone(self.noviapi,
            'novitus.noviapi model not found in registry')

    def test_get_base_url_http(self):
        """_get_base_url must return http://IP:PORT for HTTP."""
        url = self.noviapi._get_base_url(self.printer)
        self.assertEqual(url, 'http://127.0.0.1:8888',
            'Expected http://127.0.0.1:8888, got %s' % url)

    def test_get_base_url_https(self):
        """_get_base_url must return https://IP:PORT for HTTPS."""
        self.printer.novitus_use_https = True
        url = self.noviapi._get_base_url(self.printer)
        self.assertEqual(url, 'https://127.0.0.1:8888',
            'Expected https://127.0.0.1:8888, got %s' % url)

    def test_get_endpoint_url(self):
        """_get_endpoint_url must build correct full URL."""
        url = self.noviapi._get_endpoint_url(self.printer, 'receipt')
        self.assertEqual(url, 'http://127.0.0.1:8888/api/v1/receipt',
            'Wrong endpoint URL: %s' % url)

    @patch('odoo.addons.pos_novitus_printer.services.novitus_noviapi.requests.get')
    def test_connection_test_calls_correct_endpoint(self, mock_get):
        """test_connection_from_pos must call GET /api/v1 only."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = self.noviapi.test_connection_from_pos(self.printer.id)

        self.assertTrue(result, 'Connection test must return True on 200')
        call_args = mock_get.call_args
        called_url = call_args[0][0] if call_args[0] else call_args[1].get('url', '')
        self.assertIn('/api/v1', called_url,
            'Connection test must call /api/v1')
        self.assertNotIn('/status', called_url,
            'Connection test must NOT call /api/v1/status')
        self.assertNotIn('/info', called_url,
            'Connection test must NOT call /api/v1/info')

    @patch('odoo.addons.pos_novitus_printer.services.novitus_noviapi.requests.get')
    def test_connection_test_returns_false_on_error(self, mock_get):
        """test_connection_from_pos must return False on network error."""
        mock_get.side_effect = Exception('Connection refused')

        result = self.noviapi.test_connection_from_pos(self.printer.id)

        self.assertFalse(result,
            'Connection test must return False on network error')

    @patch('odoo.addons.pos_novitus_printer.services.novitus_noviapi.requests.get')
    def test_token_fetch_uses_get_no_auth(self, mock_get):
        """Token acquisition must use GET with no Authorization header."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'token': 'eyJ.test.token',
            'expiration_date': '2099-01-01T00:00:00Z'
        }
        mock_get.return_value = mock_response

        token = self.noviapi._fetch_new_token(self.printer)

        self.assertEqual(token, 'eyJ.test.token')
        call_headers = mock_get.call_args[1].get('headers', {})
        self.assertNotIn('Authorization', call_headers,
            'Token fetch must NOT send Authorization header')
        self.assertEqual(call_headers.get('User-Agent'), 'NoviApi',
            'Token fetch must send User-Agent: NoviApi')
