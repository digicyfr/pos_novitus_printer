# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    """Extend pos.order to track fiscal receipt information"""
    _inherit = 'pos.order'

    # Fiscal receipt tracking
    is_fiscal_receipt = fields.Boolean(
        string='Is Fiscal Receipt',
        default=False,
        help='Indicates if this order has been fiscalized on Novitus printer',
        readonly=True
    )

    fiscal_receipt_number = fields.Char(
        string='Fiscal Receipt Number',
        help='Unique fiscal receipt number from Novitus printer (e.g., 2025/0001234)',
        readonly=True,
        copy=False
    )

    fiscal_printer_id = fields.Char(
        string='Fiscal Printer ID',
        help='Identifier of the printer that issued the fiscal receipt',
        readonly=True,
        copy=False
    )

    fiscal_receipt_date = fields.Datetime(
        string='Fiscal Receipt Date',
        help='Date and time when fiscal receipt was printed',
        readonly=True,
        copy=False
    )

    fiscal_receipt_type = fields.Selection([
        ('paragon', 'Paragon (Receipt)'),
        ('faktura', 'Faktura (Invoice)')
    ], string='Fiscal Receipt Type', default='paragon', help='Type of fiscal document')

    # Status tracking
    fiscal_print_status = fields.Selection([
        ('pending', 'Pending'),
        ('printing', 'Printing'),
        ('printed', 'Printed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled')
    ], string='Fiscal Print Status', default='pending', readonly=True)

    fiscal_print_error = fields.Text(
        string='Fiscal Print Error',
        help='Error message if fiscal printing failed',
        readonly=True
    )

    fiscal_retry_count = fields.Integer(
        string='Retry Count',
        default=0,
        help='Number of times fiscal printing has been retried',
        readonly=True
    )

    # CRK (Central Cash Register Repository) tracking
    crk_transmitted = fields.Boolean(
        string='Transmitted to CRK',
        default=False,
        help='Indicates if receipt data has been transmitted to Central Cash Register Repository',
        readonly=True
    )

    crk_transmission_date = fields.Datetime(
        string='CRK Transmission Date',
        readonly=True
    )

    def action_print_fiscal_receipt(self):
        """
        Print fiscal receipt on Novitus printer
        Called from POS or manually
        """
        self.ensure_one()

        if self.is_fiscal_receipt and self.fiscal_receipt_number:
            raise UserError(
                _('This order already has a fiscal receipt.\nFiscal Number: %s\nPrinted: %s') % (
                    self.fiscal_receipt_number,
                    self.fiscal_receipt_date
                )
            )

        # Get Novitus printer from POS config
        printer = self.session_id.config_id.printer_ids.filtered(
            lambda p: p.printer_type == 'novitus_online'
        )[:1]

        if not printer:
            raise UserError(
                _('No Novitus fiscal printer configured for this POS.\nPlease configure a Novitus printer in POS settings.')
            )

        # Update status
        self.write({'fiscal_print_status': 'printing'})

        # Call NoviAPI service to print
        noviapi_service = self.env['novitus.noviapi']

        try:
            result = noviapi_service.print_fiscal_receipt(self, printer)

            if result.get('success'):
                # Update order with fiscal data
                self.write({
                    'is_fiscal_receipt': True,
                    'fiscal_receipt_number': result.get('fiscal_number'),
                    'fiscal_printer_id': result.get('printer_id'),
                    'fiscal_receipt_date': fields.Datetime.now(),
                    'fiscal_print_status': 'printed',
                    'fiscal_print_error': False,
                    'crk_transmitted': result.get('crk_transmitted', False),
                    'crk_transmission_date': fields.Datetime.now() if result.get('crk_transmitted') else False
                })

                _logger.info(
                    'Fiscal receipt printed successfully for order %s. Fiscal number: %s',
                    self.name,
                    result.get('fiscal_number')
                )

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Fiscal Receipt Printed'),
                        'message': _('Fiscal Number: %s\nPrinter: %s\nCRK: %s') % (
                            result.get('fiscal_number'),
                            result.get('printer_id'),
                            'Transmitted' if result.get('crk_transmitted') else 'Pending'
                        ),
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                # Print failed
                self.write({
                    'fiscal_print_status': 'failed',
                    'fiscal_print_error': result.get('error', 'Unknown error'),
                    'fiscal_retry_count': self.fiscal_retry_count + 1
                })

                _logger.error(
                    'Fiscal receipt printing failed for order %s. Error: %s',
                    self.name,
                    result.get('error')
                )

                raise UserError(
                    _('Fiscal receipt printing failed.\nError: %s\n\nPlease check:\n- Printer is online\n- Printer has paper\n- Network connection') % result.get('error')
                )

        except Exception as e:
            self.write({
                'fiscal_print_status': 'failed',
                'fiscal_print_error': str(e),
                'fiscal_retry_count': self.fiscal_retry_count + 1
            })
            _logger.exception('Exception during fiscal receipt printing for order %s', self.name)
            raise

    def action_retry_fiscal_print(self):
        """Retry fiscal printing for failed receipts"""
        self.ensure_one()

        if self.fiscal_retry_count >= 3:
            raise UserError(
                _('Maximum retry attempts reached (3).\nPlease check printer and try again later.')
            )

        return self.action_print_fiscal_receipt()

    def action_view_fiscal_receipt(self):
        """View fiscal receipt details"""
        self.ensure_one()

        return {
            'name': _('Fiscal Receipt Details'),
            'type': 'ir.actions.act_window',
            'res_model': 'pos.order',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    @api.model
    def _order_fields(self, ui_order):
        """Override to include fiscal data from POS"""
        order_fields = super()._order_fields(ui_order)

        # Add fiscal fields if present in ui_order
        if ui_order.get('fiscal_receipt_number'):
            order_fields.update({
                'is_fiscal_receipt': True,
                'fiscal_receipt_number': ui_order.get('fiscal_receipt_number'),
                'fiscal_printer_id': ui_order.get('fiscal_printer_id'),
                'fiscal_receipt_date': ui_order.get('fiscal_receipt_date'),
                'fiscal_print_status': 'printed',
                'crk_transmitted': ui_order.get('crk_transmitted', False)
            })

        return order_fields
