# POS Novitus Online Fiscal Printer

[![License: LGPL-3](https://img.shields.io/badge/license-LGPL--3-blue)](LICENSE)
[![Odoo Version](https://img.shields.io/badge/odoo-17.0-purple)](https://www.odoo.com/)

Integrate Novitus online fiscal printers with Odoo Point of Sale for Polish fiscal compliance.

## Features

- ✅ Support for Novitus online fiscal printers (POINT, HD II Online, BONO Online, DEON Online)
- ✅ NoviAPI REST protocol communication via HTTP/HTTPS
- ✅ Fiscal receipt (paragon) printing with unique fiscal numbers
- ✅ PTU (Polish VAT) rate mapping (A=23%, B=8%, C=5%, D=0%, E=exempt)
- ✅ Fiscal number tracking on POS orders
- ✅ Cash drawer control
- ✅ Error handling and offline detection
- ✅ Polish market fiscal compliance (2025)

## Requirements

- Odoo 17.0 or higher
- Python 3.10+
- Novitus online fiscal printer with NoviAPI support
- Network connectivity between Odoo server and printer
- Fiscalized printer registered with Polish tax office (KAS)

## Installation

### 1. Install Module

```bash
# Copy module to Odoo addons directory
sudo cp -r pos_novitus_printer /usr/lib/python3/dist-packages/odoo/addons/
# OR copy to custom addons path
sudo cp -r pos_novitus_printer /home/azad/.local/share/Odoo/addons/17.0/

# Restart Odoo
sudo systemctl restart odoo
```

### 2. Activate Module

1. Login to Odoo as Administrator
2. Go to **Apps**
3. Remove "Apps" filter
4. Search for "Novitus"
5. Click **Install** on "POS Novitus Online Fiscal Printer"

## Configuration

### 1. Enable NoviAPI on Printer

1. Access your Novitus printer menu
2. Navigate to: **Ustawienia → Konfiguracja → Połączenia → NOVIAPI → OPCJE**
3. Enable NoviAPI
4. Configure IP address and port (default: 8888)
5. Note the printer's IP address

### 2. Configure in Odoo

1. Go to **Point of Sale → Configuration → Point of Sale**
2. Open your POS configuration
3. Go to **Connected Devices** tab
4. Under "Receipt Printer" or "Order Printers", click **Add a line**
5. Create new printer:
   - **Name**: "Novitus Main Printer"
   - **Printer Type**: "Novitus Online Fiscal Printer"
   - **IP Address**: Your printer IP (e.g., 192.168.1.100)
   - **Port**: 8888 (or your custom port)
   - **Use HTTPS**: Enable if printer supports HTTPS
6. Click **Test Connection** to verify
7. Configure **PTU Rate Mapping**:
   - **PTU A (23%)**: Select your 23% VAT tax
   - **PTU B (8%)**: Select your 8% VAT tax
   - **PTU C (5%)**: Select your 5% VAT tax
   - **PTU D (0%)**: Select your 0% VAT tax
   - **PTU E (Exempt)**: Select your exempt tax
8. **Save**

### 3. Start Using

1. Open POS
2. Create order
3. Process payment
4. Receipt will automatically print on Novitus printer
5. Fiscal number will be displayed and stored in order

## Usage

### Printing Fiscal Receipt

Fiscal receipts are printed automatically when you complete a POS order. The fiscal number is displayed on screen and saved to the order.

### Viewing Fiscal Information

1. Go to **Point of Sale → Orders → Orders**
2. Open any order
3. Click on **Fiscal Receipt** tab
4. View fiscal number, printer ID, CRK transmission status

### Manual Fiscal Printing

If automatic printing fails, you can manually print:

1. Open the order
2. Go to **Fiscal Receipt** tab
3. Click **Print Fiscal Receipt** button

### Cash Drawer

Cash drawer opens automatically when payment is processed (if supported by printer).

## Troubleshooting

### "Cannot connect to printer"

**Causes:**
- Printer is offline
- Wrong IP address or port
- Network connectivity issues
- NoviAPI not enabled on printer

**Solutions:**
1. Check printer is powered on
2. Verify IP address: `ping <printer-ip>`
3. Check NoviAPI is enabled in printer settings
4. Verify port number (default: 8888)
5. Check firewall rules

### "Fiscal printing failed"

**Causes:**
- Printer out of paper
- Printer fiscal memory full
- Network timeout
- Invalid data

**Solutions:**
1. Check printer has paper
2. Check fiscal memory status
3. Increase timeout in settings
4. Check PTU rate mappings are correct
5. Review error message in order's "Fiscal Receipt" tab

### Fiscal number not stored

**Causes:**
- Printer not returning fiscal number in response
- Response format not recognized

**Solutions:**
1. Check printer firmware is up to date
2. Review Odoo logs: `sudo tail -f /var/log/odoo/odoo-server.log`
3. Contact support with log details

## Supported Printers

All Novitus online fiscal printers with NoviAPI support:

- **Novitus POINT** (ONLINE 3.0) ✅
- **Novitus HD II Online** (ONLINE 2.0) ✅
- **Novitus BONO Online** ✅
- **Novitus DEON Online** ✅

## Polish Fiscal Compliance

This module provides full compliance with Polish fiscal regulations (2025):

- ✅ Unique fiscal receipt numbers
- ✅ PTU (VAT) rate tracking
- ✅ Automatic CRK transmission
- ✅ Fiscal memory protection
- ✅ Daily reports support
- ✅ Paragon and faktura support

## License

This project is licensed under the LGPL-3 License - see [LICENSE](LICENSE) file.

## Author

**Azad Karipody Hamza**
- Website: https://kebabsuperking.website
- Email: azadkaripodyhamza@gmail.com

## Support

- **Issues**: Report issues on GitHub
- **Documentation**: See this README and inline code comments
- **Community**: Polish Odoo community forums

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

## Changelog

### Version 1.0.0 (2025-01-13)
- Initial release
- NoviAPI REST integration
- PTU rate mapping
- Fiscal number tracking
- Polish fiscal compliance

## Credits

- Novitus for NoviAPI protocol
- Odoo Community for POS framework
- Polish Odoo community for localization

---

**Made with ❤️ for Polish retail businesses**
