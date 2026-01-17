# Linter Quick Start Guide

## Running the Linter

Always run from the `/home/Umusa/scripts` directory:

```bash
cd /home/Umusa/scripts
```

### Lint Specific Modules

```bash
# Stock Manager module
python linter/summary.py src/stock_manager/

# Attachment Sync module
python linter/summary.py src/attachment_sync/

# All services
python linter/summary.py services/

# Specific file
python linter/summary.py src/stock_manager/config.py
```

### Lint Everything

```bash
# Lint all Python code in src/
python linter/summary.py src/

# Lint all Python code in scripts (src + services + everything)
python linter/summary.py
```

## What Gets Checked

1. **BLACK** - Auto-formats code (modifies files in place)
2. **ISORT** - Sorts imports (modifies files in place)
3. **FLAKE8** - Style guide enforcement (warnings/errors)
4. **PYDOCSTYLE** - Docstring style (Google style)
5. **DARGLINT** - Docstring/argument compliance
6. **NAMING** - Custom naming conventions

## Understanding the Output

### Console Table

```
╔════════════╦════════════╦════════════╗
║  Linter    ║ Warnings   ║ Failures   ║
╠════════════╬════════════╬════════════╣
║ BLACK      ║     0      ║     1      ║  ← 1 file reformatted
║ ISORT      ║     0      ║     0      ║  ← All imports sorted
║ FLAKE8     ║     5      ║     3      ║  ← 5 warnings, 3 errors
║ PYDOCSTYLE ║     0      ║     2      ║  ← 2 docstring issues
║ DARGLINT   ║     0      ║     4      ║  ← 4 docstring/arg mismatches
║ NAMING     ║     2      ║     0      ║  ← 2 naming warnings
╚════════════╩════════════╩════════════╝
```

### Details File

All details are written to `linter/lint-results.txt`

## Common Issues & Fixes

### 1. Black/Isort Changed Files

**Issue**: Files were auto-formatted
**Action**: Review changes with `git diff`, commit if correct

### 2. FLAKE8 Errors

Common errors:
- `E501` - Line too long (warning only, max 100 chars)
- `F401` - Unused import
- `E302` - Expected 2 blank lines

**Fix**: Edit the file to address the specific issue

### 3. PYDOCSTYLE Errors

Common errors:
- `D103` - Missing docstring in public function
- `D400` - First line should end with a period

**Fix**: Add or fix docstrings following Google style

### 4. DARGLINT Errors

Common errors:
- `DAR201` - Missing "Returns" in docstring
- `DAR101` - Missing parameter in docstring

**Fix**: Ensure docstring matches function signature

Example:
```python
def my_function(param1: int, param2: str) -> bool:
    """Short description.
    
    Args:
        param1 (int): Description of param1.
        param2 (str): Description of param2.
    
    Returns:
        bool: Description of return value.
    """
    return True
```

### 5. NAMING Warnings

Common warnings:
- Variable not snake_case
- Function not snake_case

**Fix**: Rename using snake_case (unless it's a constant like `DEFAULT_CONFIG`)

## Excluded Directories

The following directories are automatically excluded:
- `.ipynb_checkpoints`
- `__pycache__`
- `.git`
- `venv`, `.venv`
- `Notebooks`
- `OpenAI`
- `sheldonreimers`
- `wip_services`
- `Template`, `Template Scripts`
- `.pytest_cache`

## Pre-Commit Workflow

Before committing code:

```bash
# 1. Lint your changes
python linter/summary.py src/stock_manager/

# 2. Review lint-results.txt
cat linter/lint-results.txt

# 3. Fix any failures (not warnings)
# Edit files as needed

# 4. Re-run linter to confirm
python linter/summary.py src/stock_manager/

# 5. Review black/isort changes
git diff

# 6. Commit if all good
git add .
git commit -m "Your message"
```

## Configuration Files

- `.flake8` - Flake8 configuration (max line length: 100)
- `.pydocstyle` - Pydocstyle configuration (Google convention)
- `pyproject.toml` - Black, isort, and pytest configuration

## Tips

1. **Start small**: Lint one file at a time when learning
2. **Warnings vs Failures**: Warnings don't cause exit code 1
3. **Auto-fix first**: Black and isort fix most formatting issues
4. **Focus on failures**: Fix failures before worrying about warnings
5. **Docstrings matter**: Good docstrings help with code understanding

## Need Help?

See full documentation in `linter/ReadMe.md`
