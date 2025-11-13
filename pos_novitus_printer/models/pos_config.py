# -*- coding: utf-8 -*-

from odoo import models, fields


class PosConfig(models.Model):
    """Extend pos.config for Novitus printer configuration"""
    _inherit = 'pos.config'

    # Note: Novitus printer is configured through printer_ids (Many2many to pos.printer)
    # This is consistent with how Epson printers work in Odoo
    # We add helper fields here for quick access

    def get_novitus_printer(self):
        """Get the Novitus printer configured for this POS"""
        self.ensure_one()
        return self.printer_ids.filtered(lambda p: p.printer_type == 'novitus_online')[:1]

    def has_novitus_printer(self):
        """Check if this POS has a Novitus printer configured"""
        return bool(self.get_novitus_printer())
