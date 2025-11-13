# -*- coding: utf-8 -*-
{
    'name': 'POS Novitus Online Fiscal Printer',
    'version': '17.0.2.0.0',
    'category': 'Point of Sale',
    'summary': 'Free Novitus fiscal printer integration for Odoo POS - Polish compliance',

    'description': """
POS Novitus Online Fiscal Printer Integration
==============================================

FREE & OPEN SOURCE integration of Novitus online fiscal printers with Odoo POS.

Developed by Digicyfr Polska - Odoo Experts in Warsaw, Poland.

Features:
---------
* Support for Novitus online fiscal printers (POINT, HD II Online, BONO Online, DEON)
* NoviAPI REST protocol communication via HTTP/HTTPS
* Fiscal receipt (paragon) printing with unique fiscal numbers
* PTU (Polish VAT) rate mapping (A=23%, B=8%, C=5%, D=0%, E=exempt)
* Fiscal number tracking on POS orders
* Cash drawer control
* Error handling and offline detection
* Polish market fiscal compliance (2025)
* Compatible with Odoo Community & Enterprise

Supported Printers:
-------------------
* Novitus POINT (ONLINE 3.0)
* Novitus HD II Online (ONLINE 2.0)
* Novitus BONO Online
* Novitus DEON Online
* Any Novitus printer with NoviAPI support

Requirements:
-------------
* Odoo 17.0 or higher (Community or Enterprise)
* Novitus online fiscal printer with NoviAPI enabled
* Network connectivity between Odoo server and printer
* Fiscalized printer registered with Polish tax office (KAS)

Configuration:
--------------
1. Install this module
2. Go to Point of Sale → Configuration → Point of Sale
3. Open your POS configuration
4. Under "Connected Devices", click "Add Printer"
5. Select "Novitus Online Fiscal Printer"
6. Enter printer IP address and port (default: 8888)
7. Map PTU tax rates to Odoo taxes
8. Test connection
9. Save and start using POS!

Polish Market:
--------------
This module provides full compliance with Polish fiscal regulations (2025).
It supports mandatory fiscal printer requirements for retail businesses in Poland.

Need Help?
----------
Professional services available:
* Implementation & Configuration
* Custom Development & Integration
* Training & Consulting
* Odoo Enterprise Support
* Managed Services

Contact: info@digicyfr.com
Website: https://www.digicyfr.com
GitHub: https://github.com/digicyfr/pos-novitus-printer

Professional Services by Digicyfr Polska
Odoo Experts | Warsaw, Poland

License: LGPL-3
Author: Azad Karipody Hamza
Company: Digicyfr Polska
    """,

    'author': 'Digicyfr Polska',
    'maintainer': 'Azad Karipody Hamza',
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
            'pos_novitus_printer/static/src/css/novitus.css',
        ],
    },

    'images': [
        'static/description/icon.png',
        'static/description/banner.png',
        'static/description/screenshot_1.png',
        'static/description/screenshot_2.png',
        'static/description/screenshot_3.png',
    ],

    'price': 0.00,
    'currency': 'EUR',

    'installable': True,
    'application': False,
    'auto_install': False,

    'support': 'info@digicyfr.com',
}
