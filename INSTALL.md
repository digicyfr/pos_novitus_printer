# Installation Guide - POS Novitus Online Fiscal Printer

Complete step-by-step installation guide for Odoo 17.

---

## Table of Contents

1. [Pre-Installation Checklist](#pre-installation-checklist)
2. [Method 1: GitHub Installation](#method-1-github-installation-recommended)
3. [Method 2: Manual Installation](#method-2-manual-installation)
4. [Method 3: Odoo Apps Store](#method-3-odoo-apps-store)
5. [Post-Installation Configuration](#post-installation-configuration)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)

---

## Pre-Installation Checklist

Before installing, ensure you have:

### System Requirements
- [ ] Odoo 17.0 installed and running
- [ ] Python 3.10+ (included with Odoo)
- [ ] `requests` library (standard with Odoo)
- [ ] Admin/sudo access to server

### Network Requirements
- [ ] Novitus printer powered on
- [ ] Printer connected to network
- [ ] Printer IP address known
- [ ] Network connectivity between Odoo and printer
- [ ] Port 8888 accessible (default NoviAPI port)

### Odoo Requirements
- [ ] `point_of_sale` module installed
- [ ] `account` module installed
- [ ] `l10n_pl` (Polish localization) installed
- [ ] At least one POS configured

### Printer Requirements
- [ ] Novitus online fiscal printer
- [ ] NoviAPI enabled on printer
- [ ] Printer fiscalized with KAS
- [ ] Fiscal memory not full

---

## Method 1: GitHub Installation (Recommended)

Best for: Production use, version control, easy updates

### Step 1: Find Your Addons Directory

```bash
# Common locations:
# /opt/odoo/addons
# /usr/lib/python3/dist-packages/odoo/addons
# /home/odoo/.local/share/Odoo/addons/17.0
# or custom path in odoo.conf

# Check your odoo.conf
grep addons_path /etc/odoo/odoo.conf
```

### Step 2: Clone Repository

```bash
# Navigate to addons directory
cd /path/to/your/odoo/addons

# Clone the repository
git clone https://github.com/digicyfr/pos-novitus-printer.git pos_novitus_printer

# Verify files
ls -la pos_novitus_printer/
```

### Step 3: Set Permissions

```bash
# Change ownership to odoo user
sudo chown -R odoo:odoo pos_novitus_printer

# Set correct permissions
sudo chmod -R 755 pos_novitus_printer

# Verify
ls -la pos_novitus_printer/
```

### Step 4: Restart Odoo

```bash
# Restart Odoo service
sudo systemctl restart odoo

# Check status
sudo systemctl status odoo

# Watch logs (optional)
sudo tail -f /var/log/odoo/odoo-server.log
```

### Step 5: Install in Odoo UI

1. Open Odoo in browser: `http://your-server:8069`
2. Login with admin credentials
3. Go to **Settings** (⚙️ icon)
4. Scroll to bottom, click **Activate the developer mode**
5. Go to **Apps** menu (📦 icon)
6. Click **Update Apps List** button (top right)
7. Click **Update** in confirmation dialog
8. In search box, type: `novitus`
9. Find **POS Novitus Online Fiscal Printer**
10. Click **Install** button
11. Wait for installation (30-60 seconds)

**Success!** Module is now installed ✅

---

## Method 2: Manual Installation

Best for: Testing, offline installation, no git access

### Step 1: Download Module

**Option A: Download ZIP from GitHub**
```bash
# Download latest version
wget https://github.com/digicyfr/pos-novitus-printer/archive/refs/heads/main.zip

# Or download specific release
wget https://github.com/digicyfr/pos-novitus-printer/archive/refs/tags/v17.0.2.0.0.zip
```

**Option B: Download via browser**
1. Visit: https://github.com/digicyfr/pos-novitus-printer
2. Click green **Code** button
3. Click **Download ZIP**
4. Transfer to server via SFTP/SCP

### Step 2: Extract to Addons Directory

```bash
# Find addons directory
grep addons_path /etc/odoo/odoo.conf

# Extract ZIP
unzip main.zip -d /tmp/

# Move to addons directory
sudo mv /tmp/pos-novitus-printer-main /path/to/addons/pos_novitus_printer

# Or if specific version:
sudo mv /tmp/pos-novitus-printer-17.0.2.0.0 /path/to/addons/pos_novitus_printer
```

### Step 3: Set Permissions

```bash
sudo chown -R odoo:odoo /path/to/addons/pos_novitus_printer
sudo chmod -R 755 /path/to/addons/pos_novitus_printer
```

### Step 4: Restart and Install

Follow steps 4-5 from Method 1 above.

---

## Method 3: Odoo Apps Store

Best for: Odoo.sh, managed hosting, easy updates

### Step 1: Access Odoo Apps Store

1. Login to your Odoo instance
2. Go to **Apps** menu
3. Click **Apps Store** (if available)
4. Or visit: https://apps.odoo.com

### Step 2: Find Module

1. Search for: `novitus` or `pos_novitus_printer`
2. Find: **POS Novitus Online Fiscal Printer**
3. Click on module card

### Step 3: Install

1. Click **Install** button
2. Confirm installation
3. Wait for completion

**Note**: Module may require approval/review on Odoo Apps Store. If not yet published, use Method 1 or 2.

---

## Post-Installation Configuration

### Step 1: Verify Installation

1. Go to **Apps** menu
2. Remove **Apps** filter (top left)
3. Search: `novitus`
4. Should see: **POS Novitus Online Fiscal Printer** with green **Installed** badge
5. Verify version: **17.0.2.0.0**

### Step 2: Configure Printer in Novitus

Access your Novitus printer menu:

```
MENU → USTAWIENIA → API
├── NoviAPI: WŁĄCZONE (ENABLED)
├── Port: 8888
├── Protokół: HTTP (or HTTPS)
└── Adres IP: [Note this down]
```

### Step 3: Test Network Connectivity

From Odoo server:

```bash
# Ping printer
ping 192.168.1.100  # Replace with your printer IP

# Test NoviAPI endpoint
curl http://192.168.1.100:8888/api/v1

# Should return printer info (or 200 OK)
```

### Step 4: Configure in Odoo

1. **Navigate to POS Configuration**:
   - Apps menu → **Point of Sale**
   - Configuration → **Point of Sale**
   - Open your POS configuration

2. **Add Printer Device**:
   - Scroll to **Connected Devices** section
   - Click **Add a line**
   - Or click **Edit** then **Add a line**

3. **Select Printer Type**:
   - In **Printer Type** field, select: **Novitus Online Fiscal Printer**

4. **Enter Printer Details**:
   ```
   Printer Name: Novitus Main (or your choice)
   Printer Type: Novitus Online Fiscal Printer
   Printer IP: 192.168.1.100 (your printer IP)
   Printer Port: 8888
   Use HTTPS: ☐ (check only if printer has SSL)
   Cashier ID: (optional - defaults to POS user)
   Fiscal ID: (optional - printer serial/fiscal number)
   ```

5. **Configure PTU Rate Mappings**:
   
   Map your Odoo taxes to Polish PTU rates:
   
   ```
   PTU A (23%) → [Select] 23% VAT tax
   PTU B (8%)  → [Select] 8% VAT tax
   PTU C (5%)  → [Select] 5% VAT tax
   PTU D (0%)  → [Select] 0% VAT tax
   PTU E (Exempt) → [Select] Exempt tax
   ```
   
   **Important**: All taxes used in POS must be mapped!

6. **Test Connection**:
   - Click **Test Connection** button (at bottom of printer config)
   - Should see popup: "Connected successfully"
   - Popup shows: Printer model, Fiscal ID, Status
   - If fails, see [Troubleshooting](#troubleshooting)

7. **Save Configuration**:
   - Click **Save** button
   - Configuration is now complete ✅

---

## Verification

### Verify Module Installation

```bash
# Check module files exist
ls -la /path/to/addons/pos_novitus_printer/

# Check permissions
ls -la /path/to/addons/pos_novitus_printer/__manifest__.py
# Should show: odoo:odoo

# Check Odoo logs for errors
sudo tail -50 /var/log/odoo/odoo-server.log | grep -i "novitus\|error"
```

### Verify in Odoo UI

- [ ] Module shows in **Apps** with **Installed** badge
- [ ] Version is **17.0.2.0.0**
- [ ] Author is **Digicyfr Polska**
- [ ] Printer configuration available in POS settings
- [ ] Test connection succeeds
- [ ] PTU mappings configured

### Test Fiscal Receipt (Optional)

If you have a fiscalized printer ready:

1. Open POS session
2. Add a product to cart
3. Apply tax (mapped to PTU)
4. Complete payment
5. Receipt should print with fiscal number
6. Check order in backend:
   - Point of Sale → Orders → Orders
   - Open the order
   - Should see **Fiscal Receipt Number** field
   - Should see **CRK Transmitted**: Yes

---

## Troubleshooting

### Module Not Appearing in Apps List

**Problem**: Module doesn't show after installation

**Solutions**:
```bash
# 1. Check module is in correct location
ls /path/to/addons/ | grep novitus

# 2. Check addons path in config
grep addons_path /etc/odoo/odoo.conf

# 3. Restart Odoo
sudo systemctl restart odoo

# 4. Update apps list in UI
# Apps → Update Apps List

# 5. Check logs for errors
sudo tail -100 /var/log/odoo/odoo-server.log | grep -i error
```

### Permission Denied Errors

**Problem**: Module fails to load due to permissions

**Solutions**:
```bash
# Fix ownership
sudo chown -R odoo:odoo /path/to/addons/pos_novitus_printer

# Fix permissions
sudo chmod -R 755 /path/to/addons/pos_novitus_printer

# Restart Odoo
sudo systemctl restart odoo
```

### Connection Test Fails

**Problem**: "Cannot connect to printer"

**Solutions**:

1. **Verify network connectivity**:
   ```bash
   # From Odoo server
   ping [printer-ip]
   telnet [printer-ip] 8888
   curl http://[printer-ip]:8888/api/v1
   ```

2. **Check printer settings**:
   - NoviAPI must be enabled
   - Note the correct IP and port
   - Verify firewall allows port 8888

3. **Check Odoo configuration**:
   - Correct IP address entered
   - Correct port (default: 8888)
   - HTTP vs HTTPS matches printer

4. **Check firewall**:
   ```bash
   # On Odoo server
   sudo ufw allow 8888/tcp
   
   # On printer (if applicable)
   # Ensure incoming connections allowed
   ```

### Dependencies Missing

**Problem**: Module requires dependencies

**Solutions**:
```bash
# Install Python requests library (should be included with Odoo)
pip3 install requests

# Or for Odoo's Python environment
/path/to/odoo/venv/bin/pip install requests

# Restart Odoo
sudo systemctl restart odoo
```

### Module Installation Fails

**Problem**: Installation fails with error

**Solutions**:

1. **Check dependencies are installed**:
   - `point_of_sale` module
   - `account` module
   - `l10n_pl` module

2. **Check for database issues**:
   ```bash
   # View Odoo logs
   sudo tail -200 /var/log/odoo/odoo-server.log
   ```

3. **Try upgrade instead of install**:
   - Apps → search `novitus`
   - Click **Upgrade** if previously installed

4. **Check Python syntax**:
   ```bash
   python3 -m py_compile /path/to/addons/pos_novitus_printer/__manifest__.py
   ```

---

## Upgrade from Previous Version

If you have an older version installed:

### Step 1: Backup

```bash
# Backup current module
sudo cp -r /path/to/addons/pos_novitus_printer \
            /path/to/backups/pos_novitus_printer_backup_$(date +%Y%m%d)

# Backup database (recommended)
sudo -u postgres pg_dump your_database > backup_$(date +%Y%m%d).sql
```

### Step 2: Update Files

```bash
# If using Git
cd /path/to/addons/pos_novitus_printer
git pull origin main

# If manual
# Download new version and replace files
```

### Step 3: Restart Odoo

```bash
sudo systemctl restart odoo
```

### Step 4: Upgrade Module in UI

1. Go to **Apps**
2. Remove filters
3. Search: `novitus`
4. Click **Upgrade** button
5. Wait for completion

---

## Uninstallation

If you need to remove the module:

### Step 1: Uninstall in Odoo

1. Apps → search `novitus`
2. Click **Uninstall**
3. Confirm uninstallation
4. Wait for completion

### Step 2: Remove Files

```bash
# Stop Odoo
sudo systemctl stop odoo

# Remove module directory
sudo rm -rf /path/to/addons/pos_novitus_printer

# Start Odoo
sudo systemctl start odoo
```

---

## Getting Help

### Documentation
- **README.md** - General overview
- **FAQ.md** - Common questions
- **CONTRIBUTING.md** - How to contribute

### Community Support
- **GitHub Issues**: https://github.com/digicyfr/pos-novitus-printer/issues
- **Odoo Forum**: Post in Polish Localization section

### Professional Support
- **Email**: info@digicyfr.com
- **Website**: www.digicyfr.com
- **Implementation Services**: Starting at €500
- **Support Contracts**: €500-2,000/year

---

## Next Steps

After successful installation:

1. ✅ Configure printer settings
2. ✅ Map PTU tax rates
3. ✅ Test connection
4. ✅ Test fiscal receipt printing
5. ✅ Train staff on usage
6. ✅ Monitor CRK transmission

**Congratulations! Your Novitus printer is now integrated with Odoo!** 🎉

---

**Digicyfr Polska** | Warsaw, Poland
info@digicyfr.com | www.digicyfr.com
