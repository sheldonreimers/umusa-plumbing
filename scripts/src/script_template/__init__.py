"""
Template package

Modules:
- config: Configuration settings for the Template service.
- handlers: Contains API and data handlers for session management.
- processor: Contains the Template processor for managing session creation.
- tests: Unit tests for the Template package.
"""

from .config import Config
# Export commonly used modules for easier access
from .handlers import api_handlers, data_handlers
from .processor import processorTemplate

__all__ = ["api_handlers", "data_handlers", "processorTemplate", "Config"]
