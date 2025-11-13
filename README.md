# POS Novitus Online Fiscal Printer

[![License: LGPL-3](https://img.shields.io/badge/License-LGPL%20v3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0)
[![Odoo Version](https://img.shields.io/badge/Odoo-17.0-purple.svg)](https://www.odoo.com)
[![Price](https://img.shields.io/badge/Price-FREE-success.svg)](https://github.com/digicyfr/pos-novitus-printer)
[![Made in Poland](https://img.shields.io/badge/Made%20in-Poland%20🇵🇱-red.svg)](https://www.digicyfr.com)

**FREE & Open Source** integration of Novitus online fiscal printers with Odoo 17 POS.

Developed by **Digicyfr Polska** - Odoo Experts in Warsaw, Poland.

---

## ✨ Features

- ✅ **NoviAPI REST Protocol** - Modern HTTP/HTTPS communication
- ✅ **Fiscal Receipt Printing** - Full paragon support with unique fiscal numbers
- ✅ **PTU Rate Mapping** - Complete Polish VAT system (A=23%, B=8%, C=5%, D=0%, E=exempt)
- ✅ **Fiscal Number Tracking** - Automatic tracking on POS orders
- ✅ **Cash Drawer Control** - Open drawer via fiscal printer
- ✅ **CRK Transmission** - Automatic transmission to Polish tax office
- ✅ **Odoo Community & Enterprise** - Works with both editions

## 🖨️ Supported Printers

| Model | API Version | Status |
|-------|-------------|--------|
| **Novitus POINT** | ONLINE 3.0 | ✅ Fully Supported |
| **Novitus HD II Online** | ONLINE 2.0 | ✅ Fully Supported |
| **Novitus BONO Online** | ONLINE 2.0+ | ✅ Fully Supported |
| **Novitus DEON Online** | ONLINE 2.0+ | ✅ Fully Supported |

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/digicyfr/pos-novitus-printer.git

# Copy to Odoo addons
cp -r pos-novitus-printer /path/to/odoo/addons/pos_novitus_printer

# Restart Odoo
sudo systemctl restart odoo

# Install in Odoo UI
# Apps → Update Apps List → Search "novitus" → Install
```

## ⚙️ Configuration

1. **Go to**: Point of Sale → Configuration → Point of Sale
2. **Add Printer**: Novitus Online Fiscal Printer
3. **Enter Details**:
   - IP Address: [Your printer IP]
   - Port: 8888 (default)
4. **Map PTU Rates**: Configure A-E tax mappings
5. **Test Connection**: Verify connectivity
6. **Save** and start using!

## 🇵🇱 Polish Fiscal Compliance

Full compliance with Polish fiscal regulations (2025):
- Mandatory fiscal printing
- Unique fiscal numbers
- CRK transmission
- PTU rate tracking
- Complete audit trail

## 📖 Documentation

- **[Installation Guide](INSTALL.md)** - Detailed installation steps
- **[FAQ](FAQ.md)** - Common questions and answers
- **[Contributing](CONTRIBUTING.md)** - How to contribute

## 💼 Professional Services

While this module is **FREE**, we offer professional services:

- **Implementation**: Starting at €500
- **Support Contracts**: €500-2,000/year
- **Custom Development**: €75-100/hour
- **Consulting**: €100/hour

**Contact**: info@digicyfr.com | www.digicyfr.com

## 📄 License

LGPL-3 - Free to use commercially, free to modify, free to distribute.

## 👏 Credits

**Author**: Azad Karipody Hamza
**Company**: Digicyfr Polska | Warsaw, Poland
**Website**: www.digicyfr.com

---

**Made with ❤️ in Warsaw, Poland**
