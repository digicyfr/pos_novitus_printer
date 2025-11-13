# -*- coding: utf-8 -*-

from odoo import models


class PosSession(models.Model):
    """Extend pos.session to load Novitus printer data"""
    _inherit = 'pos.session'

    def _loader_params_pos_printer(self):
        """Add Novitus-specific fields to printer data loader"""
        result = super()._loader_params_pos_printer()

        # Add Novitus fields to the fields list
        novitus_fields = [
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
        ]

        # Extend the search_params fields
        if 'search_params' in result and 'fields' in result['search_params']:
            result['search_params']['fields'].extend(novitus_fields)

        return result
