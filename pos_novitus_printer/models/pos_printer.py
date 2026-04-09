# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re


class PosPrinter(models.Model):
    """Extend pos.printer to add Novitus online fiscal printer support"""
    _inherit = 'pos.printer'

    @api.model
    def _load_pos_data_fields(self, config):
        """Extend POS data loader to include Novitus fields (Odoo 19 signature)."""
        result = super()._load_pos_data_fields(config)
        result.extend([
            'novitus_printer_ip',
            'novitus_printer_port',
            'novitus_use_https',
            'novitus_fiscal_id',
            'novitus_printer_model',
            'novitus_cashier_id',
            'novitus_ptu_a_tax_id',
            'novitus_ptu_b_tax_id',
            'novitus_ptu_c_tax_id',
            'novitus_ptu_d_tax_id',
            'novitus_ptu_e_tax_id',
            'novitus_connection_status',
        ])
        return result

    printer_type = fields.Selection(
        selection_add=[
            ('novitus_online', 'Novitus Online Fiscal Printer')
        ],
        ondelete={'novitus_online': 'set default'}
    )

    # Network configuration
    novitus_printer_ip = fields.Char(
        string='Novitus Printer IP Address',
        help='IP address of Novitus online fiscal printer (e.g., 192.168.1.100)'
    )
    novitus_printer_port = fields.Integer(
        string='Novitus Printer Port',
        default=8888,
        help='Port number for NoviAPI communication (default: 8888)'
    )
    novitus_use_https = fields.Boolean(
        string='Use HTTPS',
        default=False,
        help='Use HTTPS instead of HTTP for secure communication'
    )

    # Printer identification
    novitus_fiscal_id = fields.Char(
        string='Fiscal Printer ID',
        help='Unique identifier of the fiscal printer (NIP or serial number)',
        readonly=True
    )
    novitus_printer_model = fields.Char(
        string='Printer Model',
        help='Model name (e.g., POINT, HD II Online, BONO)',
        readonly=True
    )

    # Cashier configuration
    novitus_cashier_id = fields.Char(
        string='Default Cashier ID',
        help='Default cashier identifier for fiscal receipts'
    )

    # PTU (Polish VAT) rate mapping
    # PTU A = 23% (standard rate)
    novitus_ptu_a_tax_id = fields.Many2one(
        'account.tax',
        string='PTU A (23%)',
        domain=[('type_tax_use', '=', 'sale'), ('amount', '>=', 20), ('amount', '<=', 25)],
        help='Polish VAT rate A - 23% standard rate'
    )

    # PTU B = 8% (reduced rate)
    novitus_ptu_b_tax_id = fields.Many2one(
        'account.tax',
        string='PTU B (8%)',
        domain=[('type_tax_use', '=', 'sale'), ('amount', '>=', 7), ('amount', '<=', 9)],
        help='Polish VAT rate B - 8% reduced rate'
    )

    # PTU C = 5% (reduced rate)
    novitus_ptu_c_tax_id = fields.Many2one(
        'account.tax',
        string='PTU C (5%)',
        domain=[('type_tax_use', '=', 'sale'), ('amount', '>=', 4), ('amount', '<=', 6)],
        help='Polish VAT rate C - 5% reduced rate'
    )

    # PTU D = 0% (zero rate)
    novitus_ptu_d_tax_id = fields.Many2one(
        'account.tax',
        string='PTU D (0%)',
        domain=[('type_tax_use', '=', 'sale'), ('amount', '=', 0)],
        help='Polish VAT rate D - 0% zero rate'
    )

    # PTU E = exempt
    novitus_ptu_e_tax_id = fields.Many2one(
        'account.tax',
        string='PTU E (Exempt)',
        domain=[('type_tax_use', '=', 'sale')],
        help='Polish VAT rate E - exempt from VAT'
    )

    # Status fields
    novitus_last_connection_test = fields.Datetime(
        string='Last Connection Test',
        readonly=True
    )
    novitus_connection_status = fields.Selection([
        ('connected', 'Connected'),
        ('disconnected', 'Disconnected'),
        ('error', 'Error'),
        ('unknown', 'Unknown')
    ], string='Connection Status', default='unknown', readonly=True)

    novitus_last_error = fields.Text(
        string='Last Error Message',
        readonly=True
    )

    # NoviAPI token management
    novitus_token_cache = fields.Char(
        string='Cached API Token',
        copy=False,
        help='JWT token cached from last successful NoviAPI authentication'
    )
    novitus_token_expiry = fields.Datetime(
        string='Token Expiry',
        copy=False,
        help='Expiry timestamp of the cached JWT token'
    )
    novitus_poll_timeout = fields.Integer(
        string='Status Poll Timeout (ms)',
        default=5000,
        help='Milliseconds to wait per GET status poll. Default 5000.'
    )
    novitus_max_retries = fields.Integer(
        string='Max Command Retries',
        default=3,
        help='Maximum retry attempts on 403 concurrency errors'
    )

    @api.constrains('novitus_printer_ip')
    def _check_novitus_printer_ip(self):
        """Validate IP address format"""
        for record in self:
            if record.printer_type == 'novitus_online' and record.novitus_printer_ip:
                # Basic IP validation (IPv4)
                ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
                if not re.match(ip_pattern, record.novitus_printer_ip):
                    raise ValidationError(
                        _('Invalid IP address format. Please enter a valid IPv4 address (e.g., 192.168.1.100)')
                    )

                # Check octets are in valid range
                octets = record.novitus_printer_ip.split('.')
                for octet in octets:
                    if not 0 <= int(octet) <= 255:
                        raise ValidationError(
                            _('Invalid IP address. Each number must be between 0 and 255.')
                        )

    @api.constrains('novitus_printer_port')
    def _check_novitus_printer_port(self):
        """Validate port number"""
        for record in self:
            if record.printer_type == 'novitus_online' and record.novitus_printer_port:
                if not 1 <= record.novitus_printer_port <= 65535:
                    raise ValidationError(
                        _('Invalid port number. Port must be between 1 and 65535.')
                    )

    @api.onchange('printer_type')
    def _onchange_printer_type_novitus(self):
        """Set default values when Novitus printer type is selected"""
        if self.printer_type == 'novitus_online':
            if not self.novitus_printer_port:
                self.novitus_printer_port = 8888
            if not self.novitus_cashier_id:
                self.novitus_cashier_id = 'ODOO_POS'

    def action_test_novitus_connection(self):
        """Test connection to Novitus printer with timing feedback."""
        self.ensure_one()

        if self.printer_type != 'novitus_online':
            raise ValidationError(_('This action is only available for Novitus online printers.'))

        if not self.novitus_printer_ip:
            raise ValidationError(_('Please configure the printer IP address first.'))

        # Call NoviAPI service to test connection (returns elapsed time)
        noviapi_service = self.env['novitus.noviapi']
        result = noviapi_service.test_connection(self)

        elapsed = result.get('elapsed', 0)

        # Update status fields
        self.write({
            'novitus_last_connection_test': fields.Datetime.now(),
            'novitus_connection_status': 'connected' if result.get('success') else 'error',
            'novitus_last_error': result.get('error', '') if not result.get('success') else False
        })

        # Update printer info if available
        if result.get('printer_info'):
            self.write({
                'novitus_fiscal_id': result['printer_info'].get('fiscal_id'),
                'novitus_printer_model': result['printer_info'].get('model')
            })

        # Show notification with timing
        if result.get('success'):
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Connected to Novitus printer at %s:%s (%ss)') % (
                        self.novitus_printer_ip,
                        self.novitus_printer_port,
                        elapsed,
                    ),
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Connection Failed'),
                    'message': _('Cannot connect to Novitus printer at %s:%s.\n'
                                 'Check network connection and verify NoviAPI is enabled '
                                 'on the printer (Ustawienia → NOVIAPI → Aktywna).') % (
                        self.novitus_printer_ip,
                        self.novitus_printer_port,
                    ),
                    'type': 'danger',
                    'sticky': True,
                }
            }

    def get_novitus_url(self):
        """Get complete NoviAPI base URL"""
        self.ensure_one()
        protocol = 'https' if self.novitus_use_https else 'http'
        return f'{protocol}://{self.novitus_printer_ip}:{self.novitus_printer_port}'
