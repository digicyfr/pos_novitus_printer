# -*- coding: utf-8 -*-
"""
Novitus NoviAPI Integration Service
====================================

This service provides communication with Novitus online fiscal printers
using the NoviAPI REST protocol over HTTP/HTTPS.

NoviAPI Documentation: https://noviapi.novitus.pl/en/

Supported Printers:
- Novitus POINT (ONLINE 3.0)
- Novitus HD II Online (ONLINE 2.0)
- Novitus BONO Online
- Novitus DEON Online
"""

import requests
import json
import logging
from odoo import models, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class NovitusNoviAPI(models.AbstractModel):
    """Service for communicating with Novitus printers via NoviAPI"""
    _name = 'novitus.noviapi'
    _description = 'Novitus NoviAPI Service'

    def _get_printer_url(self, printer):
        """
        Get base URL for NoviAPI communication

        Args:
            printer: pos.printer record

        Returns:
            str: Base URL (e.g., http://192.168.1.100:8888)
        """
        if not printer.novitus_printer_ip:
            raise UserError(_('Novitus printer IP address is not configured.'))

        return printer.get_novitus_url()

    def _get_headers(self):
        """
        Prepare HTTP headers for NoviAPI requests

        Returns:
            dict: HTTP headers
        """
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    def test_connection(self, printer):
        """
        Test connection to Novitus printer

        Args:
            printer: pos.printer record

        Returns:
            dict: {
                'success': bool,
                'message': str,
                'printer_info': dict (if success)
            }
        """
        try:
            base_url = self._get_printer_url(printer)
            headers = self._get_headers()

            _logger.info('Testing connection to Novitus printer at %s', base_url)

            # Try to get printer status/info
            # NoviAPI v1 uses /api/v1 prefix (discovered through research)
            # We also try legacy endpoints as fallback

            endpoints_to_try = [
                '/api/v1',              # Basic connectivity
                '/api/v1/status',       # Status with v1
                '/api/v1/info',         # Info with v1
                '/api/status',          # Fallback
                '/api/info',            # Fallback
                '/status',
                '/'
            ]

            last_error = None
            for endpoint in endpoints_to_try:
                try:
                    url = f'{base_url}{endpoint}'
                    _logger.debug('Trying endpoint: %s', url)

                    response = requests.get(
                        url,
                        headers=headers,
                        timeout=10
                    )

                    if response.status_code == 200:
                        _logger.info('Successfully connected to Novitus printer via %s', endpoint)

                        # Try to parse response
                        try:
                            data = response.json()
                        except:
                            data = {}

                        return {
                            'success': True,
                            'message': _('Connected successfully'),
                            'printer_info': {
                                'model': data.get('model', data.get('printerModel', 'Unknown')),
                                'fiscal_id': data.get('fiscalId', data.get('nip', data.get('serialNumber', 'Unknown'))),
                                'status': data.get('status', 'online'),
                                'endpoint': endpoint
                            }
                        }

                except requests.exceptions.RequestException as e:
                    last_error = str(e)
                    _logger.debug('Endpoint %s failed: %s', endpoint, e)
                    continue

            # All endpoints failed
            return {
                'success': False,
                'error': last_error or 'Cannot connect to printer. No valid endpoint found.',
                'message': _('Connection failed')
            }

        except Exception as e:
            _logger.error('Novitus connection test failed: %s', str(e))
            return {
                'success': False,
                'error': str(e),
                'message': _('Connection error')
            }

    def print_fiscal_receipt(self, order, printer):
        """
        Print fiscal receipt on Novitus printer

        This method sends the POS order data to the Novitus printer,
        which prints the fiscal receipt and transmits to CRK.

        Args:
            order: pos.order record
            printer: pos.printer record

        Returns:
            dict: {
                'success': bool,
                'fiscal_number': str (if success),
                'printer_id': str (if success),
                'crk_transmitted': bool (if success),
                'error': str (if failed)
            }
        """
        try:
            base_url = self._get_printer_url(printer)
            headers = self._get_headers()

            # Prepare receipt data
            payload = self._prepare_receipt_payload(order, printer)

            _logger.info('Sending fiscal receipt to Novitus printer for order %s', order.name)
            _logger.debug('Payload: %s', json.dumps(payload, indent=2))

            # Send to printer
            # NoviAPI v1 uses /api/v1 prefix (discovered through research)
            endpoints_to_try = [
                '/api/v1/receipt/fiscal',  # PRIMARY with v1
                '/api/receipt/fiscal',      # Fallback
                '/api/v1/receipt',          # Alternative with v1
                '/api/receipt',             # Fallback
                '/receipt/fiscal'
            ]

            last_error = None
            for endpoint in endpoints_to_try:
                try:
                    url = f'{base_url}{endpoint}'
                    _logger.debug('Trying to print via endpoint: %s', url)

                    response = requests.post(
                        url,
                        headers=headers,
                        data=json.dumps(payload),
                        timeout=30
                    )

                    if response.status_code in (200, 201):
                        result = response.json()
                        _logger.info('Fiscal receipt printed successfully via %s: %s', endpoint, result)

                        # Extract fiscal number from response
                        fiscal_number = (
                            result.get('fiscal_number') or
                            result.get('fiscalNumber') or
                            result.get('receiptNumber') or
                            result.get('receipt_number') or
                            'UNKNOWN'
                        )

                        return {
                            'success': True,
                            'fiscal_number': fiscal_number,
                            'printer_id': printer.novitus_fiscal_id or printer.novitus_printer_ip,
                            'crk_transmitted': result.get('crk_transmitted', result.get('crkTransmitted', True)),
                            'raw_response': result
                        }

                except requests.exceptions.RequestException as e:
                    last_error = str(e)
                    _logger.debug('Endpoint %s failed: %s', endpoint, e)
                    continue

            # All endpoints failed
            error_msg = last_error or 'Failed to print receipt. No valid endpoint found.'
            _logger.error('Fiscal receipt printing failed: %s', error_msg)

            return {
                'success': False,
                'error': error_msg
            }

        except Exception as e:
            error_msg = f'Failed to communicate with Novitus printer: {str(e)}'
            _logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }

    def _prepare_receipt_payload(self, order, printer):
        """
        Prepare JSON payload for NoviAPI fiscal receipt printing

        Args:
            order: pos.order record
            printer: pos.printer record

        Returns:
            dict: JSON payload for NoviAPI
        """
        company = order.company_id

        # Prepare receipt items
        items = []
        for line in order.lines:
            if line.display_type in ('line_section', 'line_note'):
                continue

            # Get PTU rate
            ptu = self._get_ptu_rate(line.tax_ids_after_fiscal_position, printer)

            items.append({
                'name': line.product_id.name or line.full_product_name,
                'quantity': line.qty,
                'price': line.price_unit,
                'vat_rate': ptu,
                'gross_amount': line.price_subtotal_incl,
                'net_amount': line.price_subtotal,
            })

        # Prepare payment information
        payment_method = 'cash'
        if order.payment_ids:
            payment = order.payment_ids[0]
            if payment.payment_method_id.type == 'bank':
                payment_method = 'card'
            elif payment.payment_method_id.type == 'pay_later':
                payment_method = 'credit'

        # Build payload
        # Note: This is a best-guess structure based on common fiscal printer APIs
        # May need adjustment based on actual NoviAPI documentation
        payload = {
            'system_identifier': order.session_id.name,
            'cashier': printer.novitus_cashier_id or order.user_id.name,
            'seller': {
                'name': company.name,
                'nip': company.vat or '',
                'address': company.street or '',
                'city': company.city or '',
                'postal_code': company.zip or '',
            },
            'buyer': {
                'name': order.partner_id.name if order.partner_id else 'Paragon',
                'nip': order.partner_id.vat if order.partner_id else '',
            },
            'items': items,
            'payment_method': payment_method,
            'total_gross': order.amount_total,
            'total_net': order.amount_total - order.amount_tax,
            'total_vat': order.amount_tax,
            'currency': order.currency_id.name,
        }

        return payload

    def _get_ptu_rate(self, taxes, printer):
        """
        Map Odoo tax to Novitus PTU rate

        Args:
            taxes: account.tax recordset
            printer: pos.printer record

        Returns:
            str: PTU rate ('A', 'B', 'C', 'D', 'E')
        """
        if not taxes:
            return 'D'  # 0% if no tax

        tax = taxes[0]

        # Check PTU mappings configured on printer
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
        if tax.amount == 23:
            return 'A'
        elif tax.amount == 8:
            return 'B'
        elif tax.amount == 5:
            return 'C'
        elif tax.amount == 0:
            return 'D'
        else:
            return 'E'  # Exempt

    def open_cashbox(self, printer):
        """
        Open cash drawer via Novitus printer

        Args:
            printer: pos.printer record

        Returns:
            dict: {'success': bool, 'error': str (if failed)}
        """
        try:
            base_url = self._get_printer_url(printer)
            headers = self._get_headers()

            endpoints_to_try = [
                '/api/v1/cashbox/open',   # PRIMARY with v1
                '/api/v1/drawer/open',    # Alternative with v1
                '/api/cashbox/open',      # Fallback
                '/api/drawer/open',       # Fallback
                '/cashbox/open'
            ]

            for endpoint in endpoints_to_try:
                try:
                    url = f'{base_url}{endpoint}'
                    response = requests.post(url, headers=headers, timeout=10)

                    if response.status_code in (200, 201):
                        _logger.info('Cash drawer opened successfully')
                        return {'success': True}

                except requests.exceptions.RequestException:
                    continue

            return {
                'success': False,
                'error': 'Failed to open cash drawer. Endpoint not found.'
            }

        except Exception as e:
            _logger.error('Failed to open cash drawer: %s', str(e))
            return {
                'success': False,
                'error': str(e)
            }

    @api.model
    def print_fiscal_receipt_from_pos(self, receipt_data, printer_id):
        """
        Print fiscal receipt from POS frontend

        Args:
            receipt_data: dict - Receipt data from JavaScript
            printer_id: int - pos.printer ID

        Returns:
            dict: Print result
        """
        printer = self.env['pos.printer'].browse(printer_id)
        if not printer.exists():
            return {
                'success': False,
                'error': 'Printer not found'
            }

        try:
            base_url = self._get_printer_url(printer)
            headers = self._get_headers()

            _logger.info('Printing fiscal receipt from POS: %s', receipt_data)

            endpoints_to_try = [
                '/api/v1/receipt/fiscal',  # PRIMARY with v1
                '/api/receipt/fiscal',      # Fallback
                '/api/v1/receipt',          # Alternative with v1
                '/api/receipt',             # Fallback
                '/receipt/fiscal'
            ]

            last_error = None
            for endpoint in endpoints_to_try:
                try:
                    url = f'{base_url}{endpoint}'
                    _logger.debug('Trying endpoint: %s', url)

                    response = requests.post(
                        url,
                        headers=headers,
                        data=json.dumps(receipt_data),
                        timeout=30
                    )

                    if response.status_code in (200, 201):
                        result = response.json()
                        _logger.info('Fiscal receipt printed: %s', result)

                        fiscal_number = (
                            result.get('fiscal_number') or
                            result.get('fiscalNumber') or
                            result.get('receiptNumber') or
                            result.get('receipt_number') or
                            'UNKNOWN'
                        )

                        return {
                            'success': True,
                            'fiscal_number': fiscal_number,
                            'printer_id': printer.novitus_fiscal_id or printer.novitus_printer_ip,
                            'crk_transmitted': result.get('crk_transmitted', result.get('crkTransmitted', True)),
                            'raw_response': result
                        }

                except requests.exceptions.RequestException as e:
                    last_error = str(e)
                    _logger.debug('Endpoint %s failed: %s', endpoint, e)
                    continue

            return {
                'success': False,
                'error': last_error or 'Failed to print. No valid endpoint found.'
            }

        except Exception as e:
            _logger.error('print_fiscal_receipt_from_pos error: %s', str(e))
            return {
                'success': False,
                'error': str(e)
            }

    @api.model
    def test_connection_from_pos(self, printer_id):
        """
        Test connection from POS frontend

        Args:
            printer_id: int - pos.printer ID

        Returns:
            dict: Connection test result
        """
        printer = self.env['pos.printer'].browse(printer_id)
        if not printer.exists():
            return {
                'success': False,
                'error': 'Printer not found'
            }

        return self.test_connection(printer)
