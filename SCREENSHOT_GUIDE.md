# Screenshot Guide for GitHub Release

To make your GitHub repository and Odoo Apps Store listing attractive, you need quality screenshots showing the module in action.

## Required Screenshots

### 1. **Module Configuration** (Priority: HIGH)
**Filename**: `01_module_configuration.png`

**How to capture**:
1. Open Odoo at http://localhost:8069
2. Go to: Point of Sale → Configuration → Point of Sale
3. Select a POS configuration
4. Scroll to "Novitus Printer Settings" section
5. Capture the configuration form showing:
   - API URL field
   - Printer ID field
   - Authentication fields
   - Timeout settings
   - "Test Connection" button

**What to show**: Clean form with example values filled in

---

### 2. **Successful Connection Test** (Priority: HIGH)
**Filename**: `02_connection_success.png`

**How to capture**:
1. In POS Configuration → Novitus Printer Settings
2. Fill in correct printer details
3. Click "Test Connection" button
4. Capture the success notification/popup

**What to show**: Green success message confirming printer connectivity

---

### 3. **POS Session with Novitus** (Priority: MEDIUM)
**Filename**: `03_pos_session.png`

**How to capture**:
1. Open POS session: Point of Sale → Dashboard → New Session
2. Show the POS interface
3. Capture a view showing:
   - Products being added to cart
   - Subtotal/Total visible
   - Payment button ready

**What to show**: Active POS session ready for fiscal printing

---

### 4. **Receipt Printing Success** (Priority: HIGH)
**Filename**: `04_receipt_printed.png`

**How to capture**:
1. Complete a sale in POS
2. Capture the success notification after fiscal receipt is sent
3. Show the order in backend with fiscal receipt number

**What to show**: Confirmation that receipt was sent to Novitus printer

---

### 5. **Module Info in Apps** (Priority: MEDIUM)
**Filename**: `05_module_info.png`

**How to capture**:
1. Go to: Apps (with developer mode enabled)
2. Search for "novitus"
3. Click on "POS Novitus Online Fiscal Printer" module
4. Capture the module information page showing:
   - Module icon
   - Description
   - Version 17.0.2.0.0
   - Author: Digicyfr Polska
   - License: LGPL-3

**What to show**: Professional module listing

---

### 6. **Error Handling Example** (Priority: LOW, Optional)
**Filename**: `06_error_handling.png`

**How to capture**:
1. Intentionally misconfigure (wrong API URL)
2. Click "Test Connection"
3. Capture the user-friendly error message

**What to show**: Clear error messages helping users troubleshoot

---

## Screenshot Best Practices

### Technical Requirements
- **Format**: PNG (preferred) or JPG
- **Resolution**: Minimum 1280x720, ideally 1920x1080
- **File size**: Keep under 1MB per image (compress if needed)

### Visual Quality
✅ Use a clean, default Odoo theme (Enterprise or Community)
✅ Hide/blur any sensitive information (real URLs, credentials)
✅ Use example data (Demo company, test products)
✅ Ensure good contrast and readability
✅ Crop to relevant areas (no unnecessary whitespace)

### What to Avoid
❌ Blurry or low-resolution images
❌ Dark mode (harder to see in documentation)
❌ Real production data or credentials
❌ Excessive UI elements outside the module
❌ Screenshots with errors (unless showing error handling)

---

## How to Capture Screenshots

### Option 1: Browser Built-in Tools
1. Firefox: `Shift + F2` → type `screenshot --fullpage`
2. Chrome: `F12` → `Ctrl+Shift+P` → "Capture screenshot"

### Option 2: Screenshot Tools
- **Linux**: Flameshot, GNOME Screenshot, Spectacle
- **Windows**: Snipping Tool, Greenshot
- **macOS**: `Cmd+Shift+4` or Cmd+Shift+5

### Option 3: From Server (Headless)
If you're on a headless server, you can use Playwright or Selenium to capture screenshots programmatically.

---

## Where to Place Screenshots

### For GitHub Repository
```
github-release/
├── README.md
├── screenshots/
│   ├── 01_module_configuration.png
│   ├── 02_connection_success.png
│   ├── 03_pos_session.png
│   ├── 04_receipt_printed.png
│   ├── 05_module_info.png
│   └── 06_error_handling.png (optional)
```

Then reference in README.md:
```markdown
## Screenshots

![Module Configuration](screenshots/01_module_configuration.png)
![Connection Test](screenshots/02_connection_success.png)
![POS Session](screenshots/03_pos_session.png)
```

### For Odoo Apps Store
When submitting to apps.odoo.com, upload screenshots in the module submission form. Use the most impactful ones (1, 2, 4, 5).

---

## Creating Screenshots Without Hardware

### If You Don't Have a Novitus Printer

You can still create valuable screenshots:

1. **Mock Configuration**: Fill in example values
   - API URL: `https://noviapi-demo.novitus.pl`
   - Printer ID: `DEMO-PRINTER-001`
   - Username: `demo_user`

2. **Use Developer Tools**: Temporarily modify success messages in browser console to show what a successful test looks like

3. **Documentation Screenshots**: Focus on configuration UI, settings, and module info

4. **Add Disclaimer**: In README, mention "Screenshots show configuration interface. Live printer connection required for actual fiscal receipts."

---

## Next Steps

After capturing screenshots:

1. Create `/home/azad/github-release/screenshots/` directory
2. Save all PNG files there
3. Update README.md with screenshot references
4. Test that images display correctly in GitHub preview
5. Compress images if needed (use tools like `pngquant` or online compressors)

---

## Quick Commands

```bash
# Create screenshots directory
mkdir -p /home/azad/github-release/screenshots

# Check image sizes
ls -lh /home/azad/github-release/screenshots/

# Compress PNGs (if needed)
# Install: sudo apt-get install optipng
optipng -o7 /home/azad/github-release/screenshots/*.png
```

---

**Tip**: Even without a physical printer, you can make your module look professional with well-crafted UI screenshots showing configuration and setup process!
