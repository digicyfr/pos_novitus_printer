# POS Novitus Online Fiscal Printer

[![License: LGPL-3](https://img.shields.io/badge/license-LGPL--3-blue)](LICENSE)
[![Odoo Version](https://img.shields.io/badge/odoo-17.0-purple)](https://www.odoo.com/)

Integrate Novitus online fiscal printers with Odoo Point of Sale for Polish fiscal compliance.

## Features

- Support for Novitus online fiscal printers (POINT, HD II Online, BONO Online, DEON Online)
- NoviAPI v1.0.4 REST protocol with JWT token authentication
- Verified 3-step command flow (POST, PUT confirm, GET poll)
- Fiscal receipt printing via direct_io serial protocol commands
- PTU (Polish VAT) rate mapping (A=23%, B=8%, C=5%, D=0%, E=exempt)
- Fiscal number and JPK ID tracking on POS orders
- Cash drawer control via direct_io
- Daily Z-report with queue safety check
- Automatic token refresh via PATCH (no rate limit consumed)
- Full error handling: 400, 401, 403, 404, 409, 429, 500, 507
- Decimal arithmetic for fiscal math (ROUND_HALF_UP, no float drift)
- Polish market fiscal compliance (2025/2026)
- Compatible with Odoo 17 Community & Enterprise

## Supported Printers

| Model | Minimum Firmware | NoviAPI |
|-------|-----------------|---------|
| Novitus POINT | ONLINE 3.0 (v1.00+) | v1 |
| Novitus HD II Online | ONLINE 2.0 (v3.50+) | v1 |
| Novitus BONO Online | v3.00+ | v1 |
| Novitus DEON Online | v3.10+ | v1 |

## Requirements

- Odoo 17.0 (Community or Enterprise)
- Python 3.10+
- Novitus online fiscal printer with NoviAPI enabled
- Network connectivity between Odoo server and printer (port 8888)
- For production: printer fiscalized and registered with Polish tax office (KAS)

## Installation

### From ZIP file

1. Download `pos_novitus_printer.zip`
2. In Odoo: **Settings > Developer Tools > Import Module**
3. Upload the ZIP file
4. Restart Odoo if prompted

### Manual installation

```bash
# Copy to your Odoo custom addons directory
cp -r pos_novitus_printer /path/to/odoo/custom_addons/

# Update addons_path in odoo.conf if needed
# addons_path = /path/to/odoo/addons,/path/to/odoo/custom_addons

# Restart Odoo
sudo systemctl restart odoo
```

### Activate

1. Login as Administrator
2. Go to **Apps**
3. Remove "Apps" filter, search for "Novitus"
4. Click **Install**

## Configuration

### 1. Enable NoviAPI on Printer

1. On the printer keypad, press **MENU**
2. Navigate: **Ustawienia > Konfiguracja > Polaczenia > NOVIAPI > OPCJE**
3. Set **Aktywna = ON**, **Protocol = HTTP**, **Port = 8888**
4. Save and restart the printer

### 2. Configure in Odoo

1. Go to **Point of Sale > Configuration > Preparation Printers**
2. Click **New**, set Printer Type to **Novitus Online Fiscal Printer**
3. Enter printer IP address and port (default: 8888)
4. Click **Test Connection** to verify
5. Map PTU tax rates:
   - **PTU A (23%)**: Select your 23% VAT tax
   - **PTU B (8%)**: Select your 8% VAT tax
   - **PTU C (5%)**: Select your 5% VAT tax
   - **PTU D (0%)**: Select your 0% VAT tax
   - **PTU E (Exempt)**: Select your exempt tax
6. Save

### 3. Start Using

1. Open POS session
2. Add products, process payment
3. Fiscal receipt prints automatically on the Novitus printer
4. Fiscal number stored in the order record

## How It Works

The module uses the NoviAPI REST protocol with a 3-step command flow:

1. **POST** `/api/v1/direct_io` — submit receipt via serial protocol commands
2. **PUT** `/api/v1/direct_io/{id}` — confirm the command
3. **GET** `/api/v1/direct_io/{id}?timeout=5000` — poll until DONE

Token management uses JWT with automatic PATCH refresh (does not count toward the 10/hour rate limit).

## Troubleshooting

### Cannot connect to printer

1. Verify printer is powered on: `ping <printer-ip>`
2. Test NoviAPI: `curl -H "User-Agent: NoviApi" http://<printer-ip>:8888/api/v1`
3. Check NoviAPI is enabled on the printer
4. Verify port 8888 is not blocked by firewall

### Fiscal printing failed

1. Check printer has paper
2. Check if daily Z-report is required (409 error)
3. Review error in order's Fiscal Receipt tab
4. Check Odoo logs for detailed error messages

### Token rate limit (429)

Reset from printer menu: **[3 SERWIS] > [3.3.1 ZEROWANIE] > [9 ZERUJ NOVIAPI] > [2 ODBLOKUJ]**

## Polish Fiscal Compliance

- Unique fiscal receipt numbers (paragon fiskalny)
- PTU (VAT) rate tracking per Polish fiscal law
- CRK (Centralne Repozytorium Kas) transmission
- Daily Z-report support
- Buyer NIP on B2B receipts (faktura do paragonu)
- Decimal arithmetic matching printer expectations (no error 20)

## License

LGPL-3 - see [LICENSE](LICENSE) file.

## Author

**Digicyfr Polska** - Odoo Experts in Warsaw, Poland

- Website: [www.digicyfr.com](https://www.digicyfr.com)
- Email: [info@digicyfr.com](mailto:info@digicyfr.com)
- GitHub: [github.com/digicyfr](https://github.com/digicyfr)

## Contributing

Contributions are welcome! Please fork the repository, create a feature branch, test thoroughly, and submit a pull request.

## Credits

- [Novitus](https://novitus.pl) for the NoviAPI protocol
- [Odoo](https://www.odoo.com) Community for the POS framework
- Polish Odoo community for localization support
