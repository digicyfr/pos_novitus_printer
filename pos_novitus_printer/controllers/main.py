# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)


class NovitusPrinterController(http.Controller):
    """HTTP endpoints for Novitus printer operations"""

    @http.route('/pos/novitus/save_fiscal_data', type='json', auth='user', methods=['POST'])
    def save_fiscal_data(self, order_id, fiscal_number, printer_id, **kwargs):
        """
        Save fiscal data to POS order from frontend

        Args:
            order_id: POS order ID
            fiscal_number: Fiscal receipt number
            printer_id: Printer identifier

        Returns:
            dict: {'success': bool}
        """
        try:
            order = request.env['pos.order'].browse(order_id)
            if order:
                order.write({
                    'is_fiscal_receipt': True,
                    'fiscal_receipt_number': fiscal_number,
                    'fiscal_printer_id': printer_id,
                    'fiscal_receipt_date': http.request.env['ir.fields'].Datetime.now(),
                    'fiscal_print_status': 'printed',
                    'crk_transmitted': kwargs.get('crk_transmitted', False)
                })
                return {'success': True}
            else:
                return {'success': False, 'error': 'Order not found'}

        except Exception as e:
            _logger.error('Failed to save fiscal data: %s', str(e))
            return {'success': False, 'error': str(e)}
