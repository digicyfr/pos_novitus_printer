# POS Novitus Online Fiscal Printer

[![License: LGPL-3](https://img.shields.io/badge/license-LGPL--3-blue)](pos_novitus_printer/LICENSE)
[![Odoo](https://img.shields.io/badge/Odoo-17%20|%2018%20|%2019-purple)](https://www.odoo.com)
[![Price](https://img.shields.io/badge/Price-FREE-success)](https://github.com/digicyfr/pos_novitus_printer)

Odoo POS integration with Novitus online fiscal printers via NoviAPI v1.0.4 — Polish fiscal compliance.

## Branches (choose your Odoo version)

| Branch | Odoo Version | Status |
|--------|-------------|--------|
| [`17.0`](https://github.com/digicyfr/pos_novitus_printer/tree/17.0) | Odoo 17 | Stable — tested |
| [`18.0`](https://github.com/digicyfr/pos_novitus_printer/tree/18.0) | Odoo 18 | Available |
| [`19.0`](https://github.com/digicyfr/pos_novitus_printer/tree/19.0) | Odoo 19 | Available |

## Features

- NoviAPI v1.0.4 REST protocol with JWT token authentication
- Verified 3-step command flow (POST, PUT confirm, GET poll)
- Fiscal receipt printing via direct_io serial protocol commands
- PTU rate mapping (A=23%, B=8%, C=5%, D=0%, E=exempt)
- Fiscal number and JPK ID tracking on POS orders
- Cash drawer control, daily Z-report with queue safety check
- Full error handling (400, 401, 403, 404, 409, 429, 500, 507)
- Decimal arithmetic for fiscal math (no float drift)

## Supported Printers

| Model | Minimum Firmware |
|-------|-----------------|
| Novitus POINT | ONLINE 3.0 (v1.00+) |
| Novitus HD II Online | ONLINE 2.0 (v3.50+) |
| Novitus BONO Online | v3.00+ |
| Novitus DEON Online | v3.10+ |

## Quick Install

1. Download ZIP from the branch matching your Odoo version
2. Extract `pos_novitus_printer/` to your custom addons directory
3. Restart Odoo, go to **Apps**, install **POS Novitus Online Fiscal Printer**

Full guide: [`docs/INSTALLATION_GUIDE.md`](pos_novitus_printer/docs/INSTALLATION_GUIDE.md)

## License

LGPL-3 — free to use, modify, and distribute.

## Author

**Digicyfr Polska** — Odoo Experts, Warsaw, Poland
- Web: [www.digicyfr.com](https://www.digicyfr.com)
- Email: [info@digicyfr.com](mailto:info@digicyfr.com)
