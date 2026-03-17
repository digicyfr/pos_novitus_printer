# POS Novitus Online Fiscal Printer — Complete Guide

**Module:** `pos_novitus_printer` v17.0.3.0.0
**Platform:** Odoo 17 (Community & Enterprise)
**License:** LGPL-3 (free and open source)
**Author:** Digicyfr Polska — www.digicyfr.com

---

## Table of Contents

1. [What This Module Does](#1-what-this-module-does)
2. [Requirements](#2-requirements)
3. [Installation](#3-installation)
4. [Printer Setup (Hardware)](#4-printer-setup-hardware)
5. [Odoo Configuration](#5-odoo-configuration)
6. [How It Works (Technical)](#6-how-it-works-technical)
7. [Daily Operations](#7-daily-operations)
8. [Error Handling](#8-error-handling)
9. [Troubleshooting](#9-troubleshooting)
10. [PTU Tax Rate Reference](#10-ptu-tax-rate-reference)
11. [Security](#11-security)
12. [Updating the Module](#12-updating-the-module)
13. [Uninstalling](#13-uninstalling)
14. [FAQ](#14-faq)
15. [Contact & Support](#15-contact--support)

---

## 1. What This Module Does

This module connects your Odoo 17 Point of Sale to a **Novitus online fiscal printer** using the **NoviAPI REST protocol**. When a cashier completes a sale in the POS, the module automatically:

1. Sends the receipt data to the Novitus printer over your local network
2. The printer prints a **fiscal receipt (paragon fiskalny)** with a unique fiscal number
3. The printer transmits the receipt to **CRK** (Centralne Repozytorium Kas — the Polish tax authority)
4. The fiscal number is stored in the Odoo order for auditing

### What printers are supported?

| Printer Model | Firmware Required | Status |
|---------------|-------------------|--------|
| Novitus POINT | ONLINE 3.0 (v1.00+) | Supported |
| Novitus HD II Online | ONLINE 2.0 (v3.50+) | Supported |
| Novitus BONO Online | v3.00+ | Supported |
| Novitus DEON Online | v3.10+ | Supported |

Any Novitus printer with **NoviAPI v1** support will work.

### What is NoviAPI?

NoviAPI is a REST API built into Novitus online fiscal printers. It allows software to communicate with the printer over HTTP/HTTPS on port 8888. This module uses NoviAPI v1.0.4 with the verified 3-step command protocol.

---

## 2. Requirements

### Software
- **Odoo 17.0** (Community or Enterprise edition)
- **Python 3.10+** (included with Odoo 17)
- **Polish localization module** (`l10n_pl`) — installed automatically as a dependency

### Hardware
- **Novitus online fiscal printer** (see supported models above)
- **Ethernet or WiFi network** connecting the Odoo server and the printer
- Printer must have **NoviAPI enabled** (see Section 4)

### Network
- The Odoo server must be able to reach the printer on **TCP port 8888**
- Static IP recommended for the printer (to avoid IP changes breaking the connection)
- If using HTTPS: a TLS certificate must be uploaded to the printer via Wiking2 software

### For Production (Live Sales)
- Printer must be **fiscalized** by an authorized Novitus service technician
- The business must be registered with the **Polish tax office (KAS)**
- An authorized technician enters your business NIP, name, and address into the printer

### For Testing
- An **unfiscalized printer** works in training mode
- Training receipts are marked **#NIEFISKALNY#** and are not sent to CRK
- No legal consequences for training receipts

---

## 3. Installation

### Method A: Install from ZIP file (recommended)

1. Download `pos_novitus_printer-17.0.3.0.0.zip`

2. Copy the ZIP to your Odoo server

3. Extract it into your Odoo custom addons directory:
   ```bash
   cd /path/to/odoo/custom_addons/
   unzip pos_novitus_printer-17.0.3.0.0.zip
   ```

4. Make sure the custom addons directory is in your `odoo.conf`:
   ```ini
   addons_path = /path/to/odoo/addons,/path/to/odoo/custom_addons
   ```

5. Restart Odoo:
   ```bash
   sudo systemctl restart odoo
   ```

6. In Odoo, go to **Apps**, remove the "Apps" filter, search for **"Novitus"**, and click **Install**.

### Method B: Install from GitHub

```bash
cd /path/to/odoo/custom_addons/
git clone https://github.com/digicyfr/pos-novitus-printer.git pos_novitus_printer
sudo systemctl restart odoo
```

Then install from the Apps menu as in Method A.

### Method C: Manual copy

```bash
# Copy the module folder to your addons path
cp -r pos_novitus_printer /path/to/odoo/custom_addons/

# Restart Odoo
sudo systemctl restart odoo
```

### Verify Installation

After installing, check in Odoo:
- Go to **Apps** > search "Novitus"
- Status should show **Installed**
- Version should show **17.0.3.0.0**

Or check via command line:
```bash
psql -U odoo -d your_database -c \
  "SELECT name, state, latest_version FROM ir_module_module WHERE name='pos_novitus_printer';"
```

Expected: `state = installed`, `latest_version = 17.0.3.0.0`

---

## 4. Printer Setup (Hardware)

### Step 4.1: Enable NoviAPI on the Printer

On the printer's physical keypad:

```
MENU
  └─ Ustawienia (3)
       └─ Konfiguracja
            └─ Polaczenia
                 └─ NOVIAPI
                      └─ OPCJE
                           Aktywna = ON
                           Protokol = HTTP
                           Port = 8888
```

Save the settings. The printer will restart.

After restart, verify: the connection info screen should show **NOVIAPI: AKTYWNA**.

### Step 4.2: Check Firmware Version

On the printer:
```
MENU > Informacje > Wersja oprogramowania
```

Note the version and compare with the minimum requirements:
- DEON Online: >= 3.10
- BONO Online: >= 3.00
- HD II Online: >= 3.50
- POINT: >= 1.00

If your firmware is below the minimum, contact an authorized Novitus service center for an update.

### Step 4.3: Assign a Static IP

1. Find the printer's MAC address:
   ```
   Printer MENU > Informacje > Siec > MAC
   ```

2. In your router's admin panel, create a **DHCP reservation** for this MAC address (e.g., `192.168.1.50`).

3. Restart the printer. Verify it gets the assigned IP.

4. Test from the Odoo server:
   ```bash
   ping 192.168.1.50
   curl -H "User-Agent: NoviApi" http://192.168.1.50:8888/api/v1
   ```
   Expected: ping succeeds, curl returns HTTP 200.

### Step 4.4: Verify Training Mode (Before Fiscalization)

If the printer is not yet fiscalized, it operates in **training mode**. Receipts will be marked:
```
#PARAGON NIEFISKALNY#
```

This is safe for testing. No data is sent to the tax authority.

---

## 5. Odoo Configuration

### Step 5.1: Create a Novitus Printer Record

1. Go to **Point of Sale > Configuration > Preparation Printers**
2. Click **New**
3. Fill in:
   - **Name:** `Novitus Kasa 1` (or any descriptive name)
   - **Printer Type:** select **Novitus Online Fiscal Printer**

4. After selecting the printer type, a **Novitus Configuration** tab appears.

### Step 5.2: Network Settings

In the Novitus Configuration tab:

| Field | Value | Notes |
|-------|-------|-------|
| **IP Address** | `192.168.1.50` | Your printer's static IP |
| **Port** | `8888` | Default NoviAPI port |
| **Use HTTPS** | Off | Enable only if TLS certificate is installed |

### Step 5.3: Test Connection

Click the **Test Connection** button.

- **Success:** Green notification showing "Connected to Novitus printer at 192.168.1.50:8888 (0.12s)"
- **Failure:** Red notification with troubleshooting instructions

### Step 5.4: Map PTU Tax Rates

PTU is the Polish fiscal printer's tax rate classification. You must map your Odoo tax records to the correct PTU letters:

| PTU Letter | Tax Rate | Description | Example Odoo Tax |
|------------|----------|-------------|------------------|
| **A** | 23% | Standard rate | "23% G" or "23% S" |
| **B** | 8% | Reduced (food, transport) | "8%" |
| **C** | 5% | Super-reduced (books, basic food) | "5%" |
| **D** | 0% | Zero rate (exports, intra-EU) | "0%" |
| **E** | Exempt | Healthcare, education, insurance | "0% Exempt" |

Select the correct Odoo tax for each PTU dropdown. The domain filter helps — it only shows sale taxes in the appropriate percentage range.

**Important:** Have your accountant verify the PTU mappings before going live. Wrong PTU mapping = wrong VAT on fiscal receipts = legal issue.

### Step 5.5: Optional Settings

| Field | Default | Description |
|-------|---------|-------------|
| **Default Cashier ID** | `ODOO_POS` | Identifier printed on receipts |
| **Status Poll Timeout** | `5000` ms | How long the printer's long-poll waits |
| **Max Command Retries** | `3` | Retry count for 403 concurrency errors |

### Step 5.6: Assign Printer to POS

1. Go to **Point of Sale > Configuration > Point of Sale**
2. Open your POS configuration
3. In the printer/devices section, add your Novitus printer
4. Save

---

## 6. How It Works (Technical)

### The 3-Step Command Flow

Every command to the Novitus printer follows this verified protocol:

```
Step A: POST /api/v1/direct_io   →  201 {request: {id: "abc...", status: "STORED"}}
Step B: PUT  /api/v1/direct_io/abc  →  200 {request: {status: "CONFIRMED"}}
Step C: GET  /api/v1/direct_io/abc?timeout=5000  →  200 {request: {status: "DONE", jpkid: 1234}}
```

- **Step A** submits the command. The printer stores it and returns a 32-character job ID.
- **Step B** confirms the command. The printer starts executing it.
- **Step C** polls for completion. The printer returns DONE when finished.

If Step B fails (e.g., network drop), the module automatically sends **DELETE** to cancel the stored job and prevent it from blocking the printer queue.

### Token Authentication

The printer uses JWT tokens:
- **GET /api/v1/token** — acquire a new token (limited to 10 per hour)
- **PATCH /api/v1/token** — refresh an existing token (unlimited, does not count toward rate limit)

The module caches the token and refreshes it via PATCH when it's about to expire (within 2 minutes of expiry). This ensures you never hit the 10/hour rate limit during normal operation.

### Receipt Construction

Receipts are sent via the `/api/v1/direct_io` endpoint using Novitus serial protocol commands wrapped in JSON:

```json
{
  "direct_io": {
    "nov_cmd": {
      "h": {"cashier": "KASA1", "system_no": "POS/001"},
      "l": [
        {"name": "Kawa", "quantity": "1", "unit_price": "5.00",
         "gross_value": "5.00", "ptu": "A"}
      ],
      "b": [{"type": 0, "value": "5.00"}],
      "y": {"total": "5.00", "buyer_nip": ""}
    }
  }
}
```

| Command | Purpose | Fields |
|---------|---------|--------|
| `h` | Begin transaction | cashier, system_no |
| `l` | Line item (one per product) | name, quantity, unit_price, gross_value, ptu |
| `b` | Payment form (one per payment method) | type (integer), value |
| `y` | Close transaction | total, buyer_nip |

### Payment Type Integers

| Value | Payment Method |
|-------|---------------|
| 0 | Cash (GOTOWKA) |
| 1 | Card (KARTA) |
| 2 | Cheque |
| 3 | Voucher |
| 4 | Other |
| 5 | Credit |
| 8 | Transfer |

### Fiscal Math

All monetary calculations use Python's `Decimal` type with `ROUND_HALF_UP` rounding. This prevents floating-point errors that would cause the printer to reject the receipt (error code 20).

Example: `Decimal('2.99') * Decimal('0.237')` = `0.71` (correct)
vs `2.99 * 0.237` = `0.7086300000000001` (float drift — would be rejected)

---

## 7. Daily Operations

### Normal Sale Flow

1. Cashier opens POS session
2. Adds products to cart
3. Clicks Payment, selects payment method, clicks Done
4. Receipt prints automatically on the Novitus printer
5. POS returns to the product screen ready for next customer

No extra button presses needed. The fiscal number is shown briefly in a notification and stored in the order.

### Viewing Fiscal Data

1. Go to **Point of Sale > Orders > Orders**
2. The **Fiscal Status** column shows:
   - **printed** (green) — receipt printed successfully
   - **failed** (red) — printing failed (retry available)
   - **pending** — not yet printed
3. Click on any order, go to the **Fiscal Receipt** tab for details:
   - Fiscal receipt number
   - Fiscal printer ID
   - Print status
   - CRK transmission status
   - Error message (if failed)

### Daily Z-Report

At the end of each business day, print the daily Z-report:

1. In POS, click **Close Session**
2. On the close-session screen, click the **Raport Dobowy (Z)** button
3. A confirmation dialog appears — click OK
4. The daily report is sent to the printer and printed

**Important:** The module checks the printer queue before sending the daily report. If there are pending jobs, it shows an error asking you to wait.

### Retrying Failed Receipts

If a receipt fails (e.g., printer was offline):

1. Go to **Point of Sale > Orders**
2. Find orders with **Fiscal Status = failed** (shown in red)
3. Open the order, go to the **Fiscal Receipt** tab
4. Click **Retry Fiscal Print**
5. The receipt will be sent to the printer again

Maximum 3 retry attempts. After that, contact your IT administrator.

---

## 8. Error Handling

The module handles all NoviAPI error codes with clear messages:

| HTTP Code | Meaning | What the Cashier Sees |
|-----------|---------|----------------------|
| **400** | Invalid data sent to printer | "Printer rejected the request" + details |
| **401** | Token expired | Auto-refreshed, retried once. Usually invisible. |
| **403** | Printer busy (another job) | Auto-retried up to 3 times with 1-second delay |
| **404** | Job not found | "Print job not found" |
| **409** | Daily report required | "Daily Z-report is required before printing" |
| **429** | Token rate limit (10/hour) | Error with printer menu reset path |
| **500** | Internal printer error | "Printer internal error" + details |
| **507** | Printer memory full | **CRITICAL** alert — contact Novitus service |

### 409 — Daily Report Required

The printer requires a daily Z-report before it can print more receipts. Go to POS > Close Session > click **Raport Dobowy (Z)**.

### 429 — Token Rate Limit

This means more than 10 new tokens were requested in 1 hour. The error message shows the exact printer menu path to reset:

```
[3 SERWIS] > [3.3.1 ZEROWANIE] > [9 ZERUJ NOVIAPI] > [2 ODBLOKUJ]
```

This should never happen in normal operation because the module uses PATCH to refresh tokens.

### 507 — Memory Full

**This is a critical error.** The printer's protected fiscal memory is full and cannot store more receipts. Contact your authorized Novitus service center immediately. Do not attempt to resolve this yourself.

---

## 9. Troubleshooting

### Problem: "Cannot connect to printer"

**Check:**
1. Is the printer powered on?
2. Run: `ping <printer-ip>` from the Odoo server
3. Run: `curl -H "User-Agent: NoviApi" http://<printer-ip>:8888/api/v1`
4. Is NoviAPI enabled? Check printer menu: Ustawienia > NOVIAPI > Aktywna = ON
5. Is port 8888 open? Check firewall rules.
6. Did the IP address change? Check the printer's current IP and update Odoo if needed.

### Problem: Receipt prints but fiscal number not stored in Odoo

**Check:**
1. Odoo logs: `grep "novitus" /var/log/odoo/odoo-server.log | tail -20`
2. Look for "DONE" status in the log — the jpkid should be there
3. Check the order in Odoo backend — the fiscal_receipt_number field should have a value

### Problem: POS freezes when printing

This should not happen with the current module. The connection test timeout is 5 seconds, and API calls timeout at 30 seconds. If the POS appears frozen:

1. Wait up to 30 seconds — it may be waiting for the printer to respond
2. If still frozen after 30 seconds, refresh the browser
3. Check the order — it should show `fiscal_print_status = failed`
4. Retry the print after fixing the printer issue

### Problem: Printer rejects receipt with error code 20

Error 20 means the gross value calculation doesn't match `round(price * quantity, 2)`. This should not happen because the module uses Decimal arithmetic. If it does:

1. Check the product price — does it have more than 2 decimal places?
2. Check the quantity — is it a very long decimal?
3. Report the exact values to support

### Problem: "Daily Z-report is required"

The printer clock has passed midnight since the last daily report. You must print a daily Z-report before the printer will accept new receipts:

1. POS > Close Session > Raport Dobowy (Z)
2. Or from backend: use the daily report functionality

### Problem: Module not found after installation

Verify:
1. The module folder `pos_novitus_printer` is in a directory listed in `addons_path` in `odoo.conf`
2. Restart Odoo: `sudo systemctl restart odoo`
3. In Apps, click "Update Apps List" before searching

---

## 10. PTU Tax Rate Reference

Polish fiscal printers use PTU (Podatek od Towarow i Uslug) letter codes for VAT rates:

| PTU | Rate | Description | Common Products |
|-----|------|-------------|-----------------|
| **A** | 23% | Standard rate | Most goods and services, electronics, clothing |
| **B** | 8% | Reduced rate | Food products, restaurant meals, transport |
| **C** | 5% | Super-reduced | Books, newspapers, some basic food items |
| **D** | 0% | Zero rate | Exports, intra-EU supplies |
| **E** | Exempt | Tax exempt | Healthcare, education, insurance, financial services |
| **Z** | Free | Free-rated | Single free rate defined on printer (rare) |

### How to verify your PTU mapping

1. Print a test receipt with one product per PTU rate
2. Check the PTU summary table at the bottom of the receipt
3. Verify each rate matches your Odoo tax configuration
4. Have your accountant sign off before going live

---

## 11. Security

### Network Security
- The printer communicates over your **local network** on port 8888
- HTTPS is supported — upload a TLS certificate via Wiking2 software
- The printer IP should not be exposed to the public internet

### Odoo Security
- The `/pos/novitus/save_fiscal_data` endpoint requires **POS Manager** role
- Fiscal data cannot be written by unauthenticated requests
- Token is stored per-printer in the database (not shared between printers)

### Fiscal Data Integrity
- Fiscal receipt numbers are assigned by the **printer hardware**, not by Odoo
- The printer's fiscal memory is tamper-protected
- CRK transmission is handled by the printer firmware, not the module
- The module does not modify fiscal numbers after they are received from the printer

---

## 12. Updating the Module

### From ZIP
1. Stop Odoo: `sudo systemctl stop odoo`
2. Replace the module folder with the new version
3. Start Odoo: `sudo systemctl start odoo`
4. Go to **Apps**, find "POS Novitus Online Fiscal Printer", click **Upgrade**

### From command line
```bash
sudo systemctl stop odoo
cp -r pos_novitus_printer /path/to/custom_addons/
sudo systemctl start odoo

# Or use odoo-bin directly:
python3 odoo-bin -c odoo.conf -d your_database -u pos_novitus_printer --stop-after-init
```

### Version check
```bash
psql -U odoo -d your_database -c \
  "SELECT latest_version FROM ir_module_module WHERE name='pos_novitus_printer';"
```

---

## 13. Uninstalling

1. Go to **Apps** in Odoo
2. Search for "Novitus"
3. Click the module, then click **Uninstall**
4. Confirm

**Note:** Uninstalling will remove:
- Novitus printer type from the printer dropdown
- All Novitus-specific fields from printer records
- Fiscal tracking fields from POS orders

It will **not** delete:
- Your POS orders
- Your sales data
- Any data in the printer's fiscal memory

---

## 14. FAQ

### Q: Does this module cost money?
**A:** No. It is free and open source under the LGPL-3 license.

### Q: Can I use it with Odoo Enterprise?
**A:** Yes, it works with both Community and Enterprise editions of Odoo 17.

### Q: Do I need an internet connection for the printer?
**A:** The printer needs a **local network** connection to the Odoo server. For CRK transmission, the printer needs internet access, but it buffers receipts locally if the internet is temporarily down.

### Q: Can two POS terminals share one printer?
**A:** Yes, but they may experience brief delays when both print simultaneously (the printer handles one job at a time). The module automatically retries on 403 concurrency errors.

### Q: What happens if the printer is offline during a sale?
**A:** The order is saved in Odoo with `fiscal_print_status = failed`. When the printer comes back online, use the **Retry Fiscal Print** button on the order.

### Q: What happens if I lose power during a print?
**A:** The module sends a DELETE to cancel any unfinished jobs. If the receipt was already printing, the printer will complete it. The printer's fiscal memory ensures no receipts are lost.

### Q: Can I use this with non-Novitus printers?
**A:** No. This module is specifically designed for Novitus printers using the NoviAPI protocol. Other Polish fiscal printer brands (Posnet, Elzab) use different protocols.

### Q: Do I need to run a daily Z-report?
**A:** Yes. Polish fiscal law requires a daily Z-report. The module provides a button on the POS close-session screen. If you forget, the printer will block new receipts until the report is printed.

### Q: Where is the fiscal data stored?
**A:** In two places:
1. **Printer's fiscal memory** — tamper-protected hardware, required by law
2. **Odoo database** — the `pos.order` table has fiscal_receipt_number, fiscal_print_status, and other tracking fields

### Q: Can I test without fiscalizing the printer?
**A:** Yes. An unfiscalized printer operates in training mode. Receipts are marked #NIEFISKALNY# and no data is sent to the tax authority.

---

## 15. Contact & Support

**Digicyfr Polska** — Odoo Experts in Warsaw, Poland

- **Website:** [www.digicyfr.com](https://www.digicyfr.com)
- **Email:** [info@digicyfr.com](mailto:info@digicyfr.com)
- **GitHub:** [github.com/digicyfr/pos-novitus-printer](https://github.com/digicyfr/pos-novitus-printer)
- **Issues:** [GitHub Issues](https://github.com/digicyfr/pos-novitus-printer/issues)

### Professional Services Available
- Module installation and configuration
- Custom development and integration
- Printer setup and fiscalization coordination
- Staff training
- Ongoing support and maintenance

---

*This document covers version 17.0.3.0.0 of pos_novitus_printer for Odoo 17.*
