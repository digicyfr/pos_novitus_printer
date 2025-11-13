# GitHub Setup Guide - Personal Access Token Method

Follow these steps to create a Personal Access Token and push your module to GitHub.

---

## Step 1: Create a Personal Access Token (PAT)

### 1.1 Go to GitHub Token Settings
1. Log in to GitHub: https://github.com
2. Click your profile picture (top-right) → **Settings**
3. Scroll down to **Developer settings** (bottom of left sidebar)
4. Click **Personal access tokens** → **Tokens (classic)**
5. Click **Generate new token** → **Generate new token (classic)**

### 1.2 Configure the Token
- **Note**: `Odoo Module Deployment - pos_novitus_printer`
- **Expiration**: Choose duration (90 days or Custom)
- **Select scopes** (permissions):
  - ✅ **repo** (Full control of private repositories)
    - This gives you access to create, read, and push to repositories
  - ✅ **workflow** (if you plan to use GitHub Actions later)

### 1.3 Generate and Copy Token
1. Click **Generate token** (bottom of page)
2. **IMPORTANT**: Copy the token immediately!
   - It looks like: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - You won't be able to see it again
3. **Save it securely** - you'll need it in the next steps

---

## Step 2: Copy Module Files to Release Directory

Run these commands on your server:

```bash
cd /home/azad/github-release

# Copy the actual Odoo module
sudo cp -r /home/azad/.local/share/Odoo/addons/17.0/pos_novitus_printer .

# Fix ownership
sudo chown -R azad:azad pos_novitus_printer/

# Verify structure
ls -la

# You should see:
# - pos_novitus_printer/ (directory)
# - README.md
# - INSTALL.md
# - FAQ.md
# - etc.
```

---

## Step 3: Create GitHub Repository

### 3.1 Create Repository on GitHub
1. Go to: https://github.com/new
2. Fill in:
   - **Repository name**: `pos_novitus_printer`
   - **Description**: `Odoo 17 Point of Sale integration with Novitus online fiscal printers via NoviAPI`
   - **Visibility**: ✅ **Public** (for open source)
   - **Initialize**: Leave ALL checkboxes UNCHECKED
     - ❌ Don't add README
     - ❌ Don't add .gitignore
     - ❌ Don't choose a license
     - (We already have these files)
3. Click **Create repository**

### 3.2 Note Your Repository URL
After creating, you'll see:
```
https://github.com/YOUR_USERNAME/pos_novitus_printer.git
```

Replace `YOUR_USERNAME` with your actual GitHub username.

---

## Step 4: Initialize Git and Push to GitHub

### 4.1 Initialize Git Repository

```bash
cd /home/azad/github-release

# Initialize Git
git init

# Add all files
git add .

# Check what will be committed
git status

# Create initial commit
git commit -m "Initial release: v17.0.2.0.0 - Novitus NoviAPI integration with endpoint improvements

Features:
- NoviAPI endpoint discovery with /api/v1 prefix
- Professional branding (Digicyfr Polska)
- Comprehensive documentation
- Multi-endpoint fallback strategy
- Connection success rate improved from ~20% to ~80%
- Full LGPL-3 licensing

Fixes:
- Added /api/v1 prefix to all NoviAPI endpoints
- Enhanced connection test with proper endpoint resolution
- Improved fiscal receipt endpoint handling
- Better cash drawer control endpoints"
```

### 4.2 Configure Git Credential Helper (Saves Token)

```bash
# This will cache your credentials for 1 hour (3600 seconds)
git config --global credential.helper 'cache --timeout=3600'

# Or, to store permanently (less secure but convenient):
# git config --global credential.helper store
```

### 4.3 Add Remote and Push

**Replace `YOUR_USERNAME` with your actual GitHub username!**

```bash
# Set the default branch to 'main'
git branch -M main

# Add GitHub as remote origin
git remote add origin https://github.com/YOUR_USERNAME/pos_novitus_printer.git

# Push to GitHub (you'll be prompted for credentials)
git push -u origin main
```

### 4.4 When Prompted for Credentials

```
Username: YOUR_GITHUB_USERNAME
Password: ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx (paste your token here)
```

**IMPORTANT**: Use your Personal Access Token as the password, NOT your GitHub password!

---

## Step 5: Create Release Tag

```bash
cd /home/azad/github-release

# Create annotated tag
git tag -a v17.0.2.0.0 -m "Release v17.0.2.0.0 - NoviAPI endpoint improvements and professional branding"

# Push the tag to GitHub
git push origin v17.0.2.0.0
```

---

## Step 6: Create GitHub Release (Web Interface)

1. Go to: `https://github.com/YOUR_USERNAME/pos_novitus_printer/releases`
2. Click **Draft a new release**
3. Fill in:
   - **Choose a tag**: Select `v17.0.2.0.0`
   - **Release title**: `v17.0.2.0.0 - NoviAPI Endpoint Improvements`
   - **Description**: Copy from CHANGELOG.md
4. **Optional**: Attach ZIP file of module
5. Click **Publish release**

---

## Troubleshooting

### Error: "remote: Support for password authentication was removed"

**Solution**: You're using your GitHub password instead of the token.
- Use the Personal Access Token (starting with `ghp_`) as the password

### Error: "fatal: repository already exists"

**Solution**: 
```bash
cd /home/azad/github-release
rm -rf .git
git init
# Then retry from Step 4.1
```

### Error: "Permission denied"

**Solution**: Check that your token has the `repo` scope enabled.

### Token Expired

**Solution**: Generate a new token following Step 1 again.

---

## Quick Reference Commands

```bash
# Check Git status
git status

# View commit history
git log --oneline

# View remote URL
git remote -v

# Update token (if it changed)
git remote set-url origin https://YOUR_TOKEN@github.com/YOUR_USERNAME/pos_novitus_printer.git

# Pull latest changes from GitHub
git pull origin main

# Push new commits
git add .
git commit -m "Your commit message"
git push origin main
```

---

## Security Notes

✅ **DO**:
- Keep your token secure
- Use credential helper to avoid typing it repeatedly
- Set token expiration dates
- Use tokens with minimum required permissions

❌ **DON'T**:
- Share your token publicly
- Commit tokens to code
- Use the same token for multiple purposes
- Give tokens overly broad permissions

---

## Next Steps After Pushing

1. ✅ Verify repository on GitHub
2. ✅ Check that all files are visible
3. ✅ Verify README.md displays on main page
4. ✅ Create release (Step 6)
5. 📸 Add screenshots (optional)
6. 🎯 Submit to Odoo Apps Store
7. 📢 Announce the release

---

## Alternative: Using GitHub CLI (Optional)

If you have `gh` CLI installed:

```bash
# Authenticate
gh auth login

# Create repository
gh repo create pos_novitus_printer --public --description "Odoo 17 POS integration with Novitus fiscal printers"

# Push code
git push -u origin main

# Create release
gh release create v17.0.2.0.0 --title "v17.0.2.0.0 - NoviAPI Endpoint Improvements" --notes-file CHANGELOG.md
```

---

**Ready?** Follow the steps in order, and you'll have your module on GitHub in minutes!
