# Frequently Asked Questions (FAQ)

Complete answers to common questions about POS Novitus Online Fiscal Printer module.

---

## 📚 Table of Contents

- [General Questions](#general-questions)
- [Technical Questions](#technical-questions)
- [Configuration Questions](#configuration-questions)
- [Usage Questions](#usage-questions)
- [Troubleshooting](#troubleshooting)
- [Business & Licensing](#business--licensing)
- [Polish Compliance](#polish-compliance)

---

## General Questions

### Is this module really free?

**Yes!** 100% free and open source under LGPL-3 license. No license fees, no hidden costs, no subscriptions. You can use it commercially without paying anything.

### What's the catch with "free"?

There's no catch! The module is free because:
1. We believe in open source
2. It benefits the Polish Odoo community
3. We offer paid professional services (implementation, support, customization)

The business model: **Module is free → Services are paid** (optional)

### Does it work with Odoo Community Edition?

**Yes!** Works with both:
- ✅ Odoo Community Edition 17.0+
- ✅ Odoo Enterprise Edition 17.0+

### Does it work with Odoo Online/SaaS?

It depends on your hosting provider. The module needs:
- Network access to your fiscal printer
- Ability to install custom modules

**Works with**:
- ✅ Self-hosted Odoo
- ✅ Odoo.sh (with VPN to printer)
- ✅ Custom hosting providers
- ⚠️ Standard Odoo.com SaaS (may have network limitations)

### What Odoo versions are supported?

Currently:
- ✅ Odoo 17.0 (tested and supported)
- 🔜 Odoo 18.0 (planned)
- ❌ Odoo 16.0 and older (not supported - may work with modifications)

### Can I use multiple Novitus printers?

**Yes!** You can configure multiple printers:
- Multiple printers per POS
- Different printers for different POS locations
- Load balancing between printers (with customization)

---

## Technical Questions

### What is NoviAPI?

NoviAPI is Novitus' REST API protocol for communicating with their online fiscal printers. It uses:
- **Protocol**: HTTP/HTTPS
- **Format**: JSON
- **Port**: 8888 (default)
- **Base URL**: `http://[printer-ip]:8888/api/v1`

### Do I need internet connection?

**For Odoo server**: No internet needed (unless hosted in cloud)
**For printer**: Yes, printer needs internet for:
- CRK transmission to tax office
- Firmware updates
- Time synchronization

**For communication**: Odoo and printer need network connection (local or VPN)

### What network requirements are there?

**Minimum**:
- Printer and Odoo server on same network (or VPN)
- Port 8888 accessible
- HTTP/HTTPS connectivity

**Recommended**:
- Static IP for printer
- Gigabit network
- Low latency (<50ms)
- Reliable connection

### Does it support HTTPS/SSL?

**Yes!** If your Novitus printer has HTTPS enabled:
1. Check "Use HTTPS" in printer configuration
2. Ensure printer has valid SSL certificate
3. Module will use HTTPS endpoints

### What programming language is it written in?

- **Backend**: Python 3.10+ (Odoo framework)
- **Frontend**: JavaScript (Odoo POS)
- **Dependencies**: Standard Odoo libraries + `requests`

### Can I modify the source code?

**Yes!** Under LGPL-3 license you can:
- ✅ Modify for your needs
- ✅ Use commercially
- ✅ Distribute modifications
- ⚠️ Must share modifications under LGPL-3
- ⚠️ Must include license notice

---

## Configuration Questions

### How do I find my printer's IP address?

**Method 1: From printer menu**:
```
MENU → USTAWIENIA → SIEĆ/NETWORK
Look for: Adres IP / IP Address
```

**Method 2: From router**:
- Login to your router admin panel
- Check DHCP client list
- Find device named "Novitus" or similar

**Method 3: Network scan**:
```bash
nmap -p 8888 192.168.1.0/24
# Look for open port 8888
```

### What are PTU rates and how do I map them?

**PTU** = Polish VAT system used by fiscal printers

| PTU Code | VAT Rate | Common Products/Services |
|----------|----------|--------------------------|
| **A** | 23% | Most goods and services |
| **B** | 8% | Some foods, services |
| **C** | 5% | Books, selected foods |
| **D** | 0% | Exports, certain services |
| **E** | Exempt | Healthcare, education |

**To map in Odoo**:
1. Create Odoo taxes with correct rates (e.g., "VAT 23%")
2. In printer configuration, map each PTU to corresponding Odoo tax
3. Example: PTU A (23%) → "VAT 23%" tax

### What if I don't have all PTU rates?

You only need to map taxes you actually use. Common setup:
- PTU A = 23% (most businesses need this)
- PTU D = 0% (for zero-rated items)

Not all businesses need B, C, or E.

### Can I test without a physical printer?

**Partially**. You can:
- ✅ Install the module
- ✅ Configure printer settings (with fake IP)
- ✅ See the UI and options
- ❌ Cannot test actual printing
- ❌ Cannot test connection
- ❌ Cannot get fiscal numbers

**For testing**: We recommend getting a fiscalized printer, even a basic model.

### Do I need to fiscalize the printer first?

**Yes!** The printer must be:
1. Fiscalized with Polish tax office (KAS)
2. Registered with your company NIP
3. Have fiscal memory initialized
4. Connected to network

**How to fiscalize**: Contact Novitus service or authorized dealer.

---

## Usage Questions

### How do fiscal receipts work?

**Flow**:
1. Customer shops in POS
2. Cashier completes payment
3. Module sends order to printer
4. Printer prints fiscal receipt (paragon)
5. Printer generates unique fiscal number
6. Printer transmits to CRK (tax office)
7. Fiscal number saved on Odoo order

**What you see**:
- Physical receipt from printer
- Fiscal number in Odoo order
- CRK transmission status

### Where can I see fiscal numbers?

**In Odoo**:
1. Point of Sale → Orders → Orders
2. Open any order
3. Look for fields:
   - **Fiscal Receipt Number**: e.g., "001/2025"
   - **Fiscal Printer ID**: Printer serial
   - **CRK Transmitted**: Yes/No
   - **Fiscal Receipt Date**: Timestamp

**On printed receipt**:
- Fiscal number at top or bottom
- Format varies by printer model

### What happens if printer is offline?

**Current behavior**:
- Error message appears
- Order saves without fiscal number
- You must manually fiscalize later

**Recommended**:
- Have backup printer
- Check printer status before shift
- Monitor CRK transmission

**Future feature** (planned):
- Offline queue
- Automatic retry
- Batch transmission when online

### Can I print non-fiscal receipts?

**Yes**, but:
- This module is specifically for fiscal receipts
- For non-fiscal receipts, use standard Odoo POS receipt printing
- You can have both: fiscal printer for legal receipts + regular printer for copies

### How do I open the cash drawer?

**Automatic** (if configured):
- Drawer opens when fiscal receipt prints
- Configure in printer settings

**Manual**:
- Use POS "Open Drawer" button
- If printer has drawer connected, it will open via module

### Can I reprint fiscal receipts?

**No!** By Polish law:
- Fiscal receipts cannot be reprinted
- Each receipt has unique fiscal number
- Reprint would violate fiscal regulations

**Alternatives**:
- Print copy (non-fiscal) from Odoo
- Customer can get duplicate from KAS system
- Print receipt summary from Odoo

---

## Troubleshooting

### "Cannot connect to printer" error

**Solutions**:

1. **Check network**:
   ```bash
   ping [printer-ip]
   ```

2. **Check NoviAPI is enabled**:
   - Printer menu → API → NoviAPI: ON

3. **Check port**:
   ```bash
   telnet [printer-ip] 8888
   ```

4. **Check firewall**:
   ```bash
   sudo ufw allow 8888/tcp
   ```

5. **Check printer is on correct network**

### "No valid endpoint found" error

**Cause**: Module couldn't find working API endpoint

**Solutions**:
1. Verify printer has NoviAPI (not older protocol)
2. Check printer firmware is up to date
3. Try different endpoints manually:
   ```bash
   curl http://[ip]:8888/api/v1
   curl http://[ip]:8888/api/v1/status
   ```
4. Contact printer manufacturer for API documentation

### Fiscal number not saved on order

**Causes**:
- Printer communication failed
- Response didn't contain fiscal number
- Network timeout

**Solutions**:
1. Check Odoo logs:
   ```bash
   sudo tail -100 /var/log/odoo/odoo-server.log | grep -i novitus
   ```
2. Verify printer printed receipt (has fiscal number)
3. Manually add fiscal number to order if needed

### CRK transmission failed

**Causes**:
- Printer has no internet
- KAS system down (rare)
- Printer not fiscalized

**Solutions**:
1. Check printer has internet connection
2. Printer menu → Network → Test connection
3. Wait and retry (automatic in most printers)
4. Check fiscal memory is not full

### PTU rate errors

**Error**: "PTU rate invalid" or similar

**Solutions**:
1. **Verify PTU mappings**:
   - All taxes used in POS must be mapped
   - Check printer configuration
   - Map each tax to A, B, C, D, or E

2. **Check tax configuration**:
   - Tax amount matches PTU rate
   - Example: 23% tax should map to PTU A

---

## Business & Licensing

### Can I use this commercially?

**Yes!** LGPL-3 license allows:
- ✅ Commercial use
- ✅ Private use
- ✅ Modification
- ✅ Distribution

**Requirements**:
- Include license and copyright notices
- Share modifications under LGPL-3 (if distributing)

### Can I sell this module?

**Technically yes**, but:
- Anyone can download it free from GitHub
- You must keep it LGPL-3 (free and open)
- You must share source code

**Better approach**:
- Offer free module
- Sell implementation/support services

### Can I get commercial support?

**Yes!** Professional services available from **Digicyfr Polska**:

- **Implementation**: €500-1,500
- **Support Contracts**: €500-2,000/year
- **Custom Development**: €75-100/hour
- **Consulting**: €100/hour

**Contact**: info@digicyfr.com | www.digicyfr.com

### Can I customize it for my needs?

**Yes!** You can:
- Modify source code
- Add features
- Fix bugs
- Integrate with other systems

**We offer custom development services** if you need help.

### Will you keep maintaining this?

**Yes!** We're committed to:
- Bug fixes
- Security updates
- Compatibility with new Odoo versions
- Community support

**Plus**: Professional support contracts available for guaranteed maintenance.

---

## Polish Compliance

### Is this legal in Poland?

**Yes!** This module helps businesses comply with Polish fiscal printer requirements (mandatory since 2020+).

### Does it meet KAS requirements?

**Yes**, when used with fiscalized Novitus printer:
- ✅ Unique fiscal numbers
- ✅ CRK transmission
- ✅ PTU rate tracking
- ✅ Fiscal memory
- ✅ Audit trail

**Important**: The printer itself must be:
- Fiscalized with KAS
- Registered to your NIP
- Properly maintained

### What if fiscal printer fails during inspection?

**By law**, you must:
1. Notify KAS within 3 days of malfunction
2. Use backup fiscal printer (recommended)
3. Repair within 7 days
4. Keep service records

**This module helps**:
- Logs all transactions
- Tracks fiscal numbers
- Shows CRK transmission status
- Provides audit trail

### Do I still need fiscal printer if using this?

**Yes!** This module doesn't replace the fiscal printer - it integrates Odoo with it.

**You need**:
- Physical Novitus fiscal printer (hardware)
- This module (software to connect them)

### How long must I keep fiscal data?

**By Polish law**:
- **5 years** for fiscal documents
- **10 years** for accounting records

**Backup recommendations**:
- Daily database backups
- Keep fiscal reports
- Archive printer fiscal memory
- Store offsite

---

## Still Have Questions?

### Community Support
- **GitHub Issues**: https://github.com/digicyfr/pos-novitus-printer/issues
- **GitHub Discussions**: https://github.com/digicyfr/pos-novitus-printer/discussions
- **Odoo Forum**: Polish Localization section

### Professional Support
- **Email**: info@digicyfr.com
- **Website**: www.digicyfr.com
- **Phone**: Available to support contract customers
- **On-site**: Available in Warsaw area

### Documentation
- **README.md**: Overview and quick start
- **INSTALL.md**: Installation guide
- **CONTRIBUTING.md**: How to contribute

---

**Digicyfr Polska** | Warsaw, Poland
info@digicyfr.com | www.digicyfr.com

*Last Updated: November 2025*
