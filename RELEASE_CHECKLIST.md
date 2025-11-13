# GitHub Release Checklist

Use this checklist to ensure your module is ready for publication on GitHub and the Odoo Apps Store.

---

## Pre-Release Checklist

### ✅ Code Quality
- [ ] All Python files have proper encoding headers (`# -*- coding: utf-8 -*-`)
- [ ] No syntax errors (`python3 -m py_compile *.py`)
- [ ] No hardcoded credentials or sensitive data
- [ ] Code follows Odoo coding guidelines
- [ ] Proper error handling in all methods
- [ ] Logging implemented for debugging

### ✅ Module Metadata
- [ ] `__manifest__.py` has correct version (17.0.2.0.0)
- [ ] Author set to "Digicyfr Polska"
- [ ] Website: http://www.digicyfr.com
- [ ] Support email: info@digicyfr.com
- [ ] Category: Point of Sale
- [ ] License: LGPL-3
- [ ] Dependencies listed correctly
- [ ] Description is clear and professional

### ✅ Documentation
- [ ] README.md created with clear description
- [ ] INSTALL.md with step-by-step installation
- [ ] FAQ.md answering common questions
- [ ] CONTRIBUTING.md for contributors
- [ ] SCREENSHOT_GUIDE.md for visual documentation
- [ ] LICENSE file included (LGPL-3)
- [ ] CHANGELOG.md documenting version history

### ✅ Testing
- [ ] Module installs without errors
- [ ] Module upgrades from previous version
- [ ] Configuration form displays correctly
- [ ] Connection test works (if printer available)
- [ ] No errors in Odoo logs after installation
- [ ] Compatible with Odoo 17.0 Community and Enterprise

### ✅ Visual Assets
- [ ] Screenshots captured (see SCREENSHOT_GUIDE.md)
- [ ] Module icon (static/description/icon.png) - 256x256px
- [ ] Banner image for Apps Store (optional, 560x280px)
- [ ] All images optimized (under 1MB each)

---

## GitHub Repository Setup

### Initial Setup
```bash
# 1. Create GitHub repository
# Go to: https://github.com/new
# Name: pos_novitus_printer
# Description: Odoo 17 Point of Sale integration with Novitus online fiscal printers via NoviAPI
# Public repository
# Don't initialize with README (we have our own)

# 2. Copy module files to release directory
cd /home/azad/github-release
cp -r /home/azad/.local/share/Odoo/addons/17.0/pos_novitus_printer .

# 3. Initialize Git repository
cd /home/azad/github-release
git init
git add .
git commit -m "Initial release: v17.0.2.0.0 - Novitus NoviAPI integration with endpoint improvements"

# 4. Add remote and push
git remote add origin https://github.com/YOUR_USERNAME/pos_novitus_printer.git
git branch -M main
git push -u origin main
```

### Create Release
```bash
# 5. Create a tagged release
git tag -a v17.0.2.0.0 -m "Release v17.0.2.0.0 - Endpoint improvements and branding"
git push origin v17.0.2.0.0

# 6. Go to GitHub → Releases → Draft a new release
# - Tag: v17.0.2.0.0
# - Title: "v17.0.2.0.0 - NoviAPI Endpoint Improvements"
# - Description: Copy from CHANGELOG.md
# - Attach module ZIP file
```

---

## GitHub Repository Checklist

- [ ] README.md displays correctly on main page
- [ ] All documentation links work
- [ ] Screenshots display properly
- [ ] LICENSE file visible
- [ ] .gitignore prevents sensitive files
- [ ] No compiled Python files (.pyc) in repo
- [ ] Release tag created (v17.0.2.0.0)
- [ ] Release notes published
- [ ] Module ZIP available for download

---

## Odoo Apps Store Submission

### Prerequisites
- [ ] Odoo.com account created
- [ ] Company profile completed (Digicyfr Polska)
- [ ] GitHub repository public and accessible

### Submission Steps

1. **Go to**: https://apps.odoo.com/apps/submit
2. **Fill in details**:
   - App name: POS Novitus Online Fiscal Printer
   - Category: Point of Sale
   - Version: 17.0
   - License: LGPL-3
   - Price: FREE (€0.00)
   - Author: Digicyfr Polska
   - Support email: info@digicyfr.com
   - Website: http://www.digicyfr.com

3. **Upload**:
   - Module ZIP file
   - Icon (256x256px PNG)
   - Screenshots (5-10 images)

4. **Description**:
   - Copy from README.md
   - Highlight key features
   - Add installation instructions
   - Include support information

5. **Links**:
   - GitHub repository URL
   - Documentation URL
   - Support URL (email or ticketing)

### Apps Store Checklist
- [ ] Module submitted to apps.odoo.com
- [ ] All required fields completed
- [ ] Screenshots uploaded and display correctly
- [ ] Description is clear and professional
- [ ] Support contact information provided
- [ ] Module tested on Odoo.sh or runbot
- [ ] Pricing set to FREE
- [ ] Tags added (fiscal, printer, novitus, pos, poland)

---

## Post-Release Tasks

### Immediate
- [ ] Announce on social media (LinkedIn, Twitter)
- [ ] Post in Odoo community forums
- [ ] Share in relevant Odoo Facebook/Slack groups
- [ ] Update company website with module information
- [ ] Send to Novitus for potential partnership

### Ongoing Maintenance
- [ ] Monitor GitHub Issues
- [ ] Respond to support emails
- [ ] Track module downloads/installs
- [ ] Plan next version features
- [ ] Update documentation as needed

---

## Marketing Checklist

### Content Creation
- [ ] Blog post about the module
- [ ] Video tutorial (optional)
- [ ] Case study if client uses it successfully
- [ ] LinkedIn article about fiscal printer integration

### Community Engagement
- [ ] Join Odoo Polish community groups
- [ ] Engage with Novitus users
- [ ] Answer questions on Odoo forums
- [ ] Contribute to Odoo community discussions

### SEO & Visibility
- [ ] Optimize README for search (keywords: Novitus, fiscal printer, Poland, POS)
- [ ] Add topics to GitHub repo (odoo, pos, fiscal-printer, novitus, poland)
- [ ] Submit to Odoo app directories
- [ ] Share on Reddit (r/Odoo if appropriate)

---

## Common Issues & Solutions

### Issue: Module not appearing in Apps
**Solution**: Apps → Update Apps List, then search again

### Issue: Permission denied during installation
**Solution**: Check file ownership, should be `odoo:odoo`

### Issue: Screenshots not displaying on GitHub
**Solution**: Ensure relative paths are correct and images are in repo

### Issue: Module fails to install
**Solution**: Check dependencies, verify Python syntax, check Odoo logs

---

## Quick Commands Reference

```bash
# Check module syntax
python3 -m py_compile /path/to/module/*.py

# Create ZIP for distribution
cd /home/azad/github-release
zip -r pos_novitus_printer_v17.0.2.0.0.zip pos_novitus_printer/

# Check file sizes
du -sh github-release/*

# Optimize images
optipng -o7 screenshots/*.png

# Test Git status
cd /home/azad/github-release
git status
git log --oneline

# Create new release tag
git tag -a v17.0.3.0.0 -m "Release description"
git push origin v17.0.3.0.0
```

---

## Success Metrics

Track these metrics to measure success:

- **Downloads**: From GitHub and Apps Store
- **Stars**: GitHub repository stars
- **Issues**: Number and resolution rate
- **Forks**: Community contributions
- **Installs**: Active installations
- **Reviews**: Ratings on Apps Store
- **Support requests**: Volume and topics

---

## Timeline Estimate

| Task | Time Estimate |
|------|---------------|
| Code review & testing | 2-4 hours |
| Documentation writing | 3-5 hours |
| Screenshot creation | 1-2 hours |
| GitHub setup | 1 hour |
| Apps Store submission | 1-2 hours |
| Marketing content | 2-4 hours |
| **Total** | **10-18 hours** |

---

## Need Help?

- **Odoo Documentation**: https://www.odoo.com/documentation/17.0/
- **GitHub Guides**: https://guides.github.com/
- **Apps Store Guidelines**: https://www.odoo.com/page/become-a-partner
- **Community Forum**: https://www.odoo.com/forum

---

**Good luck with your release!** 🚀

Remember: A well-documented, properly tested module with clear screenshots will attract more users and contributors.
