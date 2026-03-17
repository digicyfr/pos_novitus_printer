# -*- coding: utf-8 -*-
{
    'name': 'POS Novitus Online Fiscal Printer',
    'version': '18.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Novitus fiscal printer integration for Odoo POS via NoviAPI - Polish compliance',

    'description': """
POS Novitus Online Fiscal Printer Integration
==============================================

Integration of Novitus online fiscal printers with Odoo POS
using the NoviAPI v1.0.4 REST protocol.

Developed by Digicyfr Polska - Odoo Experts in Warsaw, Poland.

Features:
---------
* NoviAPI v1.0.4 REST protocol with JWT token authentication
* Verified 3-step command flow (POST, PUT confirm, GET poll)
* Fiscal receipt printing via direct_io serial protocol commands
* PTU (Polish VAT) rate mapping (A=23%, B=8%, C=5%, D=0%, E=exempt)
* Fiscal number and JPK ID tracking on POS orders
* Cash drawer control via direct_io
* Daily Z-report with queue safety check
* Automatic token refresh via PATCH (no rate limit consumed)
* Full error handling: 400, 401, 403, 404, 409, 429, 500, 507
* Decimal arithmetic for fiscal math (ROUND_HALF_UP)
* Polish market fiscal compliance (2025/2026)

Supported Printers:
-------------------
* Novitus POINT (ONLINE 3.0)
* Novitus HD II Online (ONLINE 2.0)
* Novitus BONO Online
* Novitus DEON Online
* Any Novitus printer with NoviAPI v1 support

Requirements:
-------------
* Odoo 17.0 (Community or Enterprise)
* Novitus online fiscal printer with NoviAPI enabled
* Network connectivity between Odoo server and printer (port 8888)

License: LGPL-3

Website: https://www.digicyfr.com
Contact: info@digicyfr.com
GitHub: https://github.com/digicyfr/pos-novitus-printer
    """,

    'author': 'Digicyfr Polska',
    'maintainer': 'Digicyfr Polska',
    'website': 'https://www.digicyfr.com',
    'license': 'LGPL-3',

    'depends': [
        'point_of_sale',
        'account',
        'l10n_pl',  # Polish localization
    ],

    'data': [
        'security/ir.model.access.csv',
        'data/pos_novitus_data.xml',
        'views/pos_printer_views.xml',
        'views/pos_config_views.xml',
        'views/pos_order_views.xml',
    ],

    'assets': {
        'point_of_sale._assets_pos': [
            'pos_novitus_printer/static/src/app/novitus_printer.js',
            'pos_novitus_printer/static/src/overrides/models/models.js',
            'pos_novitus_printer/static/src/overrides/components/novitus_close_pos.js',
            'pos_novitus_printer/static/src/overrides/components/novitus_close_pos.xml',
            'pos_novitus_printer/static/src/css/novitus.css',
        ],
    },

    'images': [
        'static/description/icon.png',
        'static/description/banner.png',
    ],

    'price': 0.00,
    'currency': 'EUR',

    'installable': True,
    'application': False,
    'auto_install': False,

    'support': 'info@digicyfr.com',
}
