"""Unified linter and formatter runner for Python repo."""

import subprocess
import sys
from pathlib import Path

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
]


def should_exclude(path):
    """Return True if path should be excluded (in EXCLUDE_DIRS).

    Args:
        path (Path or str): File or directory path to check.

    Returns:
        bool: True if path contains any EXCLUDE_DIRS component.
    """
    return any(part in exclude_dirs for part in Path(path).parts)


def get_python_files(target, allow_excluded: bool = False):
    """Recursively find all Python files, optionally including excluded directories.

    If `allow_excluded` is False (the default) files or directories that contain
    any component from `exclude_dirs` will be skipped. If `allow_excluded` is
    True, the provided `target` will be returned even if it matches an excluded
    directory (useful when the user explicitly requested a path).

    Args:
        target (str or Path): Root file or directory to search.
        allow_excluded (bool): If True, ignore `exclude_dirs` when selecting files.

    Returns:
        list: List of string paths to Python files.
    """
    path = Path(target).resolve()
    if path.is_file() and str(path).endswith(".py"):
        return [str(path)] if (allow_excluded or not should_exclude(path)) else []
    elif path.is_dir():
        return [str(f) for f in path.rglob("*.py") if (allow_excluded or not should_exclude(f))]
    else:
        return []


def run_command(cmd):
    """Run a command and return (stdout+stderr, exit code).

    Args:
        cmd (list): List of command-line strings.

    Returns:
        tuple: (output (str), exit code (int))
    """
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return result.stdout, result.returncode


def extract_black_changed_files(output):
    """Returns list of reformatted files by black.

    Args:
        output (str): The output from black --verbose.

    Returns:
        list: List of reformatted file paths.
    """
    return [
        line.split("reformatted ")[1]
        for line in output.splitlines()
        if line.strip().startswith("reformatted ")
    ]


def extract_isort_changed_files(output):
    """Returns list of files fixed by isort.

    Args:
        output (str): The output from isort --verbose.

    Returns:
        list: List of fixed file paths.
    """
    return [
        line.split("Fixing ")[1]
        for line in output.splitlines()
        if line.strip().startswith("Fixing ")
    ]


def count_linter_failures(linter, output):
    """Count failures for given linter based on its output.

    Args:
        linter (str): The name of the linter.
        output (str): The output from the linter.

    Returns:
        int: Number of failures.
    """
    lines = [line for line in output.splitlines() if line.strip()]
    if not lines or (len(lines) == 1 and "No issues found" in lines[0]):
        return 0
    if linter == "flake8":
        return sum(":" in line for line in lines)
    if linter == "pydocstyle":
        return sum(":" in line for line in lines)
    return len(lines)


def count_naming_warnings(output):
    """Count warnings from the custom naming linter.

    Args:
        output (str): Output from naming_checks.py.

    Returns:
        int: Number of warnings.
    """
    return sum(1 for line in output.splitlines() if line.strip())


def is_flake8_line_length(line):
    """Return True if flake8 line is an E501 line length violation.

    Args:
        line (str): Line of flake8 output.

    Returns:
        bool: True if this line is E501.
    """
    return "E501" in line


def is_pydocstyle_line_length(line):
    """Return True if pydocstyle line describes a docstring line too long.

    Args:
        line (str): Line of pydocstyle output.

    Returns:
        bool: True if this line reports a line length issue.
    """
    return "line too long" in line or "exceeds" in line


def print_table(issue_stats):
    """Print the console summary table of warnings and failures.

    Args:
        issue_stats (dict): Dict of {linter: {"warnings": int, "failures": int}}.
    """
    print("╔════════════╦════════════╦════════════╗")
    print("║  Linter    ║ Warnings   ║ Failures   ║")
    print("╠════════════╬════════════╬════════════╣")
    for linter in issue_stats:
        warnings = issue_stats[linter]["warnings"]
        failures = issue_stats[linter]["failures"]
        print(f"║ {linter:<10} ║ {warnings:^10} ║ {failures:^10} ║")
    print("╚════════════╩════════════╩════════════╝")
    print("\nSee linter/lint-results.txt for details.\n")


def main():
    """Run all linters, print summary table, and write details to file."""
    args = sys.argv[1:]
    target = args[0] if args else "."
    # If the user provided a target on the command line, assume they want to
    # lint that path even if it lives inside an excluded directory. If no
    # target was provided, adhere to the exclusions.
    allow_excluded = bool(args)
    python_files = get_python_files(target, allow_excluded=allow_excluded)
    if not python_files:
        print(f"No Python files found under {target}")
        sys.exit(0)

    black_cmd = ["black", "--verbose"] + python_files
    isort_cmd = ["isort", "--verbose"] + python_files

    commands = [
        ("black", black_cmd),
        ("isort", isort_cmd),
        ("flake8", ["flake8"] + python_files),
        ("pydocstyle", ["pydocstyle"] + python_files),
        ("darglint", ["darglint"] + python_files),
        (
            "naming",
            [sys.executable, str(Path(__file__).parent / "naming_checks.py")] + python_files,
        ),
    ]

    details = []
    issue_stats = {}
    failed = False

    for name, cmd in commands:
        out, exitcode = run_command(cmd)
        warnings = 0
        failures = 0
        section = f"\n=== {name.upper()} ==="

        if name == "black":
            changed_files = extract_black_changed_files(out)
            failures = len(changed_files)
            details.append(section)
            if changed_files:
                details.extend(changed_files)
            else:
                details.append("All Good, No errors & warnings.")
        elif name == "isort":
            changed_files = extract_isort_changed_files(out)
            failures = len(changed_files)
            details.append(section)
            if changed_files:
                details.extend(changed_files)
            else:
                details.append("All Good, No errors & warnings.")
        else:
            details.append(section)
            lines = [line for line in out.splitlines() if line.strip()]
            if name == "flake8":
                for line in lines:
                    if "E501" in line:
                        warnings += 1
                    else:
                        failures += 1
            elif name == "pydocstyle":
                for line in lines:
                    if "line too long" in line or "exceeds" in line:
                        warnings += 1
                    else:
                        failures += 1
            elif name == "naming":
                warnings = len(lines)
            else:
                failures = len(lines)
            if lines:
                details.extend(lines)
            else:
                details.append("All Good, No errors & warnings.")

        issue_stats[name.upper()] = {"warnings": warnings, "failures": failures}
        if failures > 0 and name != "naming":
            failed = True

    print_table(issue_stats)

    # Write details to file
    result_file = Path(__file__).parent / "lint-results.txt"
    result_file.write_text("\n".join(details), encoding="utf-8")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
