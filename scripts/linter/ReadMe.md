# Python Linter

This directory contains the unified Python linter and code formatter for this repository.
It auto-formats, checks code style, and warns about naming or docstring issues—helping everyone keep the codebase clean and consistent.

---

## Features

| Feature                  | Description                                                            |
| ------------------------ | ---------------------------------------------------------------------- |
| Auto-formats code        | Uses `black` and `isort` to auto-fix Python files                      |
| Lints for style errors   | Runs `flake8` and `pydocstyle`                                         |
| Enforces docstrings      | Ensures Google-style docstrings (see below for required style)         |
| Darglint checks          | Strict docstring/argument compliance                                   |
| Custom warnings          | Warns about naming convention and docstring line length issues         |
| Summary table            | Prints warnings and failures per linter in the console                 |
| Clean output             | Only lists changed files for formatters in details file                |
| Detailed results         | All details written to `linter/lint-results.txt`                       |
| Custom exclusions        | Easily skip junk or custom folders by editing `EXCLUDE_DIRS` in script |
| Directory/file targeting | Lint whole repo, a directory, or a specific `.py` file                 |

---

## Usage

| Command                                    | What It Does                               |
| ------------------------------------------ | ------------------------------------------ |
| `python linter/summary.py`                 | Auto-fixes and lints all code in scripts/  |
| `python linter/summary.py src/`            | Lint only Python files in `src/`           |
| `python linter/summary.py services/`       | Lint only Python files in `services/`      |
| `python linter/summary.py path/to/file.py` | Lint and format a specific file            |

* **No flags needed:** Auto-fixes with `black` and `isort` every run.
* **Working directory:** Run from `/home/Umusa/scripts` directory

---

## Output

* **Console:** Table summarizing number of warnings and failures per linter.
* **Details:** See `linter/lint-results.txt` for:

  * List of files changed by black/isort
  * Full flake8, pydocstyle, and custom warning details

---

## Custom Exclusions

* To exclude certain folders, edit the `exclude_dirs` list at the top of `linter/summary.py`:

  ```python
  exclude_dirs = [
      ".ipynb_checkpoints",
      "__pycache__",
      ".Trash-0",
      "wip_services",
      "Template",
      "Template Scripts",
      ".pytest_cache",
      ".git",
      "venv",
      ".venv",
      "Notebooks",
      "OpenAI",
      "sheldonreimers",
      # Add more as needed
  ]
  ```

---

## Configuration

| Tool           | Config File               | Notes                                            |
| -------------- | ------------------------- | ------------------------------------------------ |
| black          | `pyproject.toml`          | Formatting only                                  |
| isort          | `pyproject.toml`          | Import sorting, follows `black` profile          |
| flake8         | `.flake8`                 | Use `.flake8` INI file in project root, not TOML |
| pydocstyle     | `.pydocstyle`             | Use `.pydocstyle` INI file in project root       |
| darglint       | Uses same as flake8       | Enforces Google-style docstrings                 |
| naming\_checks | `linter/naming_checks.py` | Custom linting logic                             |

* **Note:** Most tools read their config from `pyproject.toml`, but `flake8` and `pydocstyle` must use their respective dotfiles for consistent results in CI and Docker.

---

## Docstring Style Guide (Google Style + Darglint Compliance)

* All public functions/classes require **Google-style docstrings**.
* Every argument in the signature must be listed under `Args:`, types must match, and descriptions must not be omitted.
* For parameters with a default (e.g., `verbose: bool = True`), use `(bool)`, not `(bool, optional)`, unless the type is `Optional[bool]`.
* List `Returns:` and `Raises:` (only for explicitly raised exceptions) when applicable.
* Example for a method:

  ```python
  def my_func(self, param1: int, flag: bool = False) -> None:
      """
      Short summary.

      Args:
          param1 (int): Description of param1.
          flag (bool): If True, does something extra. Defaults to False.

      Returns:
          variable
      """
  ```
* Do **not** add a `Returns:` section for `__init__`.
* Only list exceptions under `Raises:` that are explicitly raised.

---

## Contributing & Extending

| How To Add / Change      | What To Do                                                   |
| ------------------------ | ------------------------------------------------------------ |
| Exclude more folders     | Add names to `EXCLUDE_DIRS`                                  |
| Add more custom checks   | Edit or extend `linter/naming_checks.py`                     |
| Add more linters/tools   | Update `commands` in `summary.py` and list required packages |
| Change formatting rules  | Update `pyproject.toml` at the repo root                     |
| Required Python packages | Install from `services/requirements.txt`                     |

---

## How It Works

| Linter         | Fixes Code | Prints Errors | Warns (doesn’t fail) | Excluded by `EXCLUDE_DIRS` |
| -------------- | ---------- | ------------- | -------------------- | -------------------------- |
| black          | Yes        | Yes           | No                   | Yes                        |
| isort          | Yes        | Yes           | No                   | Yes                        |
| flake8         | No         | Yes           | No                   | Yes                        |
| pydocstyle     | No         | Yes           | No                   | Yes                        |
| darglint       | No         | Yes           | No                   | Yes                        |
| naming\_checks | No         | No            | Yes (warnings only)  | Yes                        |

---

## FAQ

| Question                               | Answer                                                              |
| -------------------------------------- | ------------------------------------------------------------------- |
| Does it change my code?                | Yes, black and isort always auto-format (in place)                  |
| How do I see what files changed?       | Changed files are listed under each linter in `lint-results.txt`    |
| How do I ignore a folder?              | Add its name to `EXCLUDE_DIRS` in `summary.py`                      |
| How do I add another linter?           | Add it to the `commands` list in `summary.py`                       |
| Where do I configure formatting rules? | In `pyproject.toml` at the repo root (except for flake8/pydocstyle) |

---

## Example Output

**Console:**

```
╔════════════╦════════════╦════════════╗
║  Linter    ║ Warnings   ║ Failures   ║
╠════════════╬════════════╬════════════╣
║ BLACK      ║     0      ║     1      ║
║ ISORT      ║     0      ║     2      ║
║ FLAKE8     ║     0      ║     5      ║
║ PYDOCSTYLE ║     0      ║     2      ║
║ NAMING     ║     3      ║     0      ║
╚════════════╩════════════╩════════════╝

See linter/lint-results.txt for details.
```

---

**lint-results.txt (example):**

```
=== BLACK ===
/home/user/project/module.py

=== ISORT ===
/home/user/project/module.py

=== FLAKE8 ===
module.py:10:1: E302 expected 2 blank lines, found 1

=== NAMING ===
module.py:7: Class 'mymodule' not PascalCase
```

---

## Questions?

For improvements, bug reports, or questions, open a merge request or contact the maintainers.

---