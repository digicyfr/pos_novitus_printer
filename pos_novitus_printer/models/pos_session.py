# -*- coding: utf-8 -*-
# Odoo 18: Data loading handled by pos.load.mixin on pos.printer model.
# The _loader_params_pos_printer method from Odoo 17 no longer exists.
# See pos_printer.py → _load_pos_data_fields() for the Odoo 18 equivalent.

from odoo import models


class PosSession(models.Model):
    _inherit = 'pos.session'
