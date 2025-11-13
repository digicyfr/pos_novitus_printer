# Contributing to POS Novitus Online Fiscal Printer

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

---

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Community](#community)

---

## Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone, regardless of:
- Age, body size, disability
- Ethnicity, gender identity
- Experience level
- Nationality, personal appearance
- Race, religion
- Sexual identity and orientation

### Our Standards

**Positive behavior**:
- ✅ Using welcoming and inclusive language
- ✅ Being respectful of differing viewpoints
- ✅ Gracefully accepting constructive criticism
- ✅ Focusing on what is best for the community
- ✅ Showing empathy towards other community members

**Unacceptable behavior**:
- ❌ Trolling, insulting/derogatory comments
- ❌ Public or private harassment
- ❌ Publishing others' private information
- ❌ Other unethical or unprofessional conduct

---

## How Can I Contribute?

### 🐛 Reporting Bugs

Found a bug? Help us fix it!

**Before submitting**:
1. Check [existing issues](https://github.com/digicyfr/pos-novitus-printer/issues)
2. Verify it's actually a bug (not configuration issue)
3. Test with latest version

**When reporting, include**:
- **Odoo version**: e.g., 17.0 Community
- **Module version**: e.g., 17.0.2.0.0
- **Printer model**: e.g., Novitus POINT
- **Steps to reproduce**: Detailed steps
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Logs**: Relevant Odoo logs
- **Screenshots**: If applicable

**Example**:
```markdown
**Bug**: Cannot connect to printer

**Environment**:
- Odoo: 17.0 Community Edition
- Module: 17.0.2.0.0
- Printer: Novitus HD II Online
- OS: Ubuntu 22.04

**Steps to Reproduce**:
1. Configure printer with IP 192.168.1.100
2. Click "Test Connection"
3. Error appears

**Expected**: Connection success
**Actual**: "Cannot connect to printer" error

**Logs**:
```
[timestamp] ERROR novitus: Connection refused
```

**Additional context**: Printer works with NoviStudio app
```

### ✨ Suggesting Features

Have an idea? We'd love to hear it!

**Before suggesting**:
1. Check [existing feature requests](https://github.com/digicyfr/pos-novitus-printer/issues?q=is%3Aissue+is%3Aopen+label%3Aenhancement)
2. Consider if it fits project scope
3. Think about implementation

**When suggesting, include**:
- **Use case**: Why is this needed?
- **Proposed solution**: How would it work?
- **Alternatives**: Other ways to solve it?
- **Additional context**: Screenshots, examples

**Example**:
```markdown
**Feature**: Batch fiscal report export

**Use Case**: 
Business needs to export all fiscal receipts for accounting at month-end.

**Proposed Solution**:
Add "Export Fiscal Receipts" button in POS Orders view that exports CSV/PDF of all fiscal transactions in date range.

**Alternatives**:
- Manual export from Orders view (current)
- Custom report module

**Would you implement this?**: Yes, if guidance provided
```

### 🧪 Testing

Help us test with real printers!

**Testing areas**:
- Different Novitus printer models
- Different network configurations
- Edge cases and error scenarios
- Performance with high volume
- Multi-printer setups

**Report results**:
```markdown
**Test**: Novitus BONO Online printing

**Setup**:
- Printer: Novitus BONO Online (firmware 1.2.3)
- Network: WiFi, 192.168.1.105
- Odoo: 17.0 Community, Ubuntu 22.04

**Tests Performed**:
- ✅ Connection test: Success
- ✅ Single receipt: Success (fiscal no. 123/2025)
- ✅ CRK transmission: Success
- ✅ Cash drawer: Success
- ⚠️ HTTPS: Not tested (no SSL on printer)
- ❌ Bulk printing: Failed after 10 receipts

**Findings**:
Connection stable for small volumes. Issue with rapid consecutive prints (buffer overflow?).
```

### 📝 Improving Documentation

Documentation is crucial!

**Areas to improve**:
- Fix typos, grammar
- Add examples
- Clarify confusing sections
- Translate to other languages
- Add screenshots/videos
- Update outdated info

**How to contribute docs**:
1. Find documentation files (*.md)
2. Click "Edit" on GitHub
3. Make changes
4. Submit pull request

### 💻 Contributing Code

Ready to code? Awesome!

---

## Development Setup

### Prerequisites

- Odoo 17.0 development environment
- Python 3.10+
- Git
- Novitus printer (for testing) or willingness to test logic only

### Setup Development Environment

```bash
# 1. Fork the repository on GitHub
# (Click "Fork" button)

# 2. Clone your fork
git clone https://github.com/YOUR-USERNAME/pos-novitus-printer.git
cd pos-novitus-printer

# 3. Add upstream remote
git remote add upstream https://github.com/digicyfr/pos-novitus-printer.git

# 4. Create development branch
git checkout -b feature/my-feature

# 5. Link to Odoo addons
ln -s $(pwd) /path/to/odoo/addons/pos_novitus_printer

# 6. Restart Odoo with dev mode
./odoo-bin --dev=all --addons-path=/path/to/addons

# 7. Install module in Odoo UI
# Apps → Update Apps List → Install pos_novitus_printer
```

### Development Workflow

```bash
# 1. Sync with upstream
git fetch upstream
git merge upstream/main

# 2. Create feature branch
git checkout -b feature/my-awesome-feature

# 3. Make changes
# ... edit files ...

# 4. Test changes
# ... test in Odoo ...

# 5. Commit changes
git add .
git commit -m "Add awesome feature"

# 6. Push to your fork
git push origin feature/my-awesome-feature

# 7. Open Pull Request on GitHub
```

---

## Pull Request Process

### Before Submitting PR

- [ ] Code follows [Odoo coding guidelines](https://www.odoo.com/documentation/17.0/contributing/development/coding_guidelines.html)
- [ ] All tests pass (if applicable)
- [ ] Documentation updated
- [ ] Commit messages are clear
- [ ] Branch is up-to-date with main
- [ ] No merge conflicts

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tested with real printer (model: ___)
- [ ] Tested without printer (logic only)
- [ ] Added unit tests
- [ ] Manual testing performed

## Checklist
- [ ] Code follows Odoo style guidelines
- [ ] Self-reviewed code
- [ ] Commented complex code
- [ ] Updated documentation
- [ ] No new warnings
- [ ] Tested all PTU rates
- [ ] Tested error scenarios

## Screenshots (if applicable)
<!-- Add screenshots -->

## Related Issues
Closes #123
```

### Review Process

1. **Automatic checks**: CI/CD runs (if configured)
2. **Code review**: Maintainer reviews code
3. **Testing**: Ideally tested with real printer
4. **Feedback**: You may need to make changes
5. **Approval**: Once approved, maintainer merges
6. **Release**: Included in next version

---

## Coding Standards

### Python Code Style

Follow [Odoo coding guidelines](https://www.odoo.com/documentation/17.0/contributing/development/coding_guidelines.html):

**Good**:
```python
class NovitusNoviAPI(models.AbstractModel):
    """Service for communicating with Novitus printers via NoviAPI"""
    _name = 'novitus.noviapi'
    _description = 'Novitus NoviAPI Service'
    
    def test_connection(self, printer):
        """
        Test connection to Novitus printer
        
        Args:
            printer: pos.printer record
            
        Returns:
            dict: Connection result
        """
        try:
            base_url = self._get_printer_url(printer)
            # ... implementation ...
        except Exception as e:
            _logger.error('Connection test failed: %s', str(e))
            return {'success': False, 'error': str(e)}
```

**Bad**:
```python
class noviapi:  # No docstring, wrong naming
    def test(self,p):  # Unclear args, no docstring
        try:
            u=p.get_url()  # Single letter variables
            #do stuff
        except:  # Bare except
            pass  # Silent failure
```

### Code Organization

```
pos_novitus_printer/
├── __init__.py          # Module imports
├── __manifest__.py      # Module metadata
├── models/              # Odoo models
│   ├── __init__.py
│   ├── pos_printer.py   # Printer configuration
│   └── pos_order.py     # Order extensions
├── services/            # External services
│   ├── __init__.py
│   └── novitus_noviapi.py  # NoviAPI communication
├── controllers/         # HTTP controllers
├── views/               # XML views
├── data/                # Data files
├── static/              # JS, CSS, images
├── security/            # Access rights
└── tests/               # Unit tests
```

### Naming Conventions

- **Models**: `snake_case` e.g., `pos_printer.py`
- **Classes**: `PascalCase` e.g., `NovitusNoviAPI`
- **Methods**: `snake_case` e.g., `test_connection`
- **Variables**: `snake_case` e.g., `base_url`
- **Constants**: `UPPER_SNAKE_CASE` e.g., `DEFAULT_PORT`
- **Private methods**: `_snake_case` e.g., `_get_printer_url`

### Docstrings

Always include docstrings:

```python
def print_fiscal_receipt(self, order, printer):
    """
    Print fiscal receipt on Novitus printer
    
    This method sends the POS order data to the Novitus printer,
    which prints the fiscal receipt and transmits to CRK.
    
    Args:
        order (pos.order): POS order record
        printer (pos.printer): Printer configuration record
        
    Returns:
        dict: {
            'success': bool,
            'fiscal_number': str (if success),
            'error': str (if failed)
        }
        
    Raises:
        UserError: If printer not configured
    """
    # Implementation...
```

### Logging

Use proper logging levels:

```python
import logging
_logger = logging.getLogger(__name__)

# Info: Normal operations
_logger.info('Printing fiscal receipt for order %s', order.name)

# Debug: Detailed debug info
_logger.debug('Payload: %s', json.dumps(payload, indent=2))

# Warning: Unexpected but handled
_logger.warning('Endpoint %s failed, trying next', endpoint)

# Error: Error conditions
_logger.error('Failed to print receipt: %s', str(e))
```

### Error Handling

Always handle errors gracefully:

```python
# Good
try:
    result = self._send_request(url, payload)
    return {'success': True, 'data': result}
except requests.exceptions.Timeout:
    _logger.error('Request timeout to %s', url)
    return {'success': False, 'error': 'Connection timeout'}
except requests.exceptions.ConnectionError as e:
    _logger.error('Connection error: %s', str(e))
    return {'success': False, 'error': 'Cannot reach printer'}
except Exception as e:
    _logger.error('Unexpected error: %s', str(e))
    return {'success': False, 'error': str(e)}

# Bad
try:
    result = self._send_request(url, payload)
except:  # Bare except
    pass  # Silent failure
```

---

## Testing Guidelines

### Manual Testing Checklist

Before submitting PR, test:

**Connection**:
- [ ] Test connection succeeds
- [ ] Test connection fails gracefully
- [ ] HTTPS mode (if printer supports)
- [ ] Wrong IP/port shows error

**Fiscal Receipt**:
- [ ] Single receipt prints
- [ ] Fiscal number captured
- [ ] CRK transmission status shown
- [ ] PTU A (23%) works
- [ ] PTU B, C, D, E work (if applicable)
- [ ] Zero-tax products work

**Error Scenarios**:
- [ ] Printer offline handled
- [ ] Network down handled
- [ ] Invalid endpoint handled
- [ ] Timeout handled

**Multi-configuration**:
- [ ] Multiple printers per POS
- [ ] Different PTU mappings
- [ ] HTTP and HTTPS printers

### Unit Tests (Future)

If adding unit tests:

```python
# tests/test_novitus_noviapi.py
from odoo.tests import TransactionCase

class TestNovitusNoviAPI(TransactionCase):
    def setUp(self):
        super().setUp()
        self.printer = self.env['pos.printer'].create({
            'name': 'Test Printer',
            'printer_type': 'novitus_online',
            'novitus_printer_ip': '192.168.1.100',
            'novitus_printer_port': 8888,
        })
        
    def test_get_printer_url(self):
        """Test URL generation"""
        service = self.env['novitus.noviapi']
        url = service._get_printer_url(self.printer)
        self.assertEqual(url, 'http://192.168.1.100:8888')
```

---

## Documentation

### Updating Documentation

When changing code, update relevant docs:

- **README.md**: If adding major features
- **INSTALL.md**: If changing installation
- **FAQ.md**: If fixing common issues
- **Code comments**: Always document complex logic

### Documentation Style

- Use clear, simple language
- Include examples
- Add code blocks with syntax highlighting
- Use emojis for visual appeal (✅❌⚠️🔧📝)
- Keep paragraphs short
- Use bullet points and tables

---

## Community

### Getting Help

- **GitHub Discussions**: Ask questions
- **GitHub Issues**: Report bugs, request features
- **Email**: info@digicyfr.com (for private matters)

### Contributors

Thank you to all contributors!

<!-- Add contributors list -->

### Recognition

- Contributors will be listed in README
- Significant contributions will be credited
- We appreciate every contribution!

---

## Questions?

**Not sure where to start?**

Look for issues labeled:
- `good first issue` - Perfect for first-time contributors
- `help wanted` - We need help here
- `documentation` - Improve docs

**Contact us**:
- Email: info@digicyfr.com
- GitHub: Open an issue
- Website: www.digicyfr.com

---

Thank you for contributing! 🎉

**Digicyfr Polska** | Warsaw, Poland
