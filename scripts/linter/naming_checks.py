"""Custom naming and docstring linter for the project."""

import ast
import sys


def is_snake_case(name):
    """Return True if name is snake_case (including single words).

    Args:
        name (str): Variable name to check.

    Returns:
        bool: True if name is snake_case.
    """
    return name.islower() and not any(c.isupper() for c in name) and "-" not in name


def is_pascal_case(name):
    """Return True if name is PascalCase.

    Args:
        name (str): Class name to check.

    Returns:
        bool: True if name is PascalCase.
    """
    return name[0].isupper() and "_" not in name and not name.isupper()


def check_file(file_path, max_doc_line=100):
    """Check file for naming and docstring line length issues.

    Args:
        file_path (str): Path to the Python file to check.
        max_doc_line (int, optional): Maximum allowed docstring line length. Defaults to 100.

    Returns:
        list: List of warning strings found in the file.
    """
    warnings = []
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=file_path)

    for node in ast.walk(tree):
        # Check classes
        if isinstance(node, ast.ClassDef):
            # if not is_pascal_case(node.name):
            #     warnings.append(f"{file_path}:{node.lineno}: Class '{node.name}' not PascalCase")
            # Docstring line length
            doc = ast.get_docstring(node)
            if doc:
                for i, line in enumerate(doc.splitlines(), 1):
                    if len(line) > max_doc_line:
                        warnings.append(
                            f"{file_path}:{node.lineno + i}: "
                            f"Class docstring line exceeds {max_doc_line} chars"
                        )
        # Check functions
        if isinstance(node, ast.FunctionDef):
            if not is_snake_case(node.name):
                warnings.append(f"{file_path}:{node.lineno}: Function '{node.name}' not snake_case")
            # Docstring line length
            doc = ast.get_docstring(node)
            if doc:
                for i, line in enumerate(doc.splitlines(), 1):
                    if len(line) > max_doc_line:
                        warnings.append(
                            f"{file_path}:{node.lineno + i}: "
                            f"Function docstring line exceeds {max_doc_line} chars"
                        )
        # Check variables (simple only)
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if not is_snake_case(target.id):
                        warnings.append(
                            f"{file_path}:{target.lineno}: Variable '{target.id}' not snake_case"
                        )
    return warnings


def main():
    """Run naming and docstring line length checks for files given on the command line."""
    files = sys.argv[1:]
    all_warnings = []
    for file in files:
        all_warnings.extend(check_file(file))
    for w in all_warnings:
        print(w)
    sys.exit(0)  # Always zero (warnings only)


if __name__ == "__main__":
    main()
