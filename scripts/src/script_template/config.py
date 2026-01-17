"""Config {{ ModuleName }} for scripts.

This module is intentionally simple and importable without rendering.
When you want a concrete `config.py` for a service, render this file
with Jinja2 or copy-and-replace the placeholders.
"""


class Config:
    """Holds configuration for a script/service."""

    def __init__(self):
        # Basic metadata used by `main.py` and tests.
        self.name = "script_template"
        self.version = "0.1.0"
        self.debug = True

        # Universal/service-scoped ID (example).
        self.UniversalID = "UniversalID"

        # placeholders as strings so imports succeed pre-render.
        self.TemplateDetail = TemplateDetails(
            TemplateVariable='Template Variable Value'
        )

    def __repr__(self):
        return (
            f"Config("
            f"name='{self.name}', "
            f"version='{self.version}', "
            f"debug={self.debug}, "
            f"UniversalID='{self.UniversalID}', "
            f"TemplateDetails={self.TemplateDetail}"
            f")"
        )


class TemplateDetails:
    """Reusable {{ ModuleName }} class for channel/message details.

    Accepts rendered values or Jinja2 placeholders left as strings.
    """

    def __init__(self, TemplateVariable):
        self.TemplateVariable = TemplateVariable

    def __repr__(self):
        return (
            f"TemplateDetails("
            f"TemplateVariable='{self.TemplateVariable}', "
            f")"
        )

# Default instance for tests and quick smoke runs.
DEFAULT_CONFIG = Config()
