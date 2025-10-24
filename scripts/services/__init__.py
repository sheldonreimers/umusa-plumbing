"""Initialise the config module."""

# Import core services that are always needed
from .Logger import Logger
from .SecretManager import SecretManager

# Import services with optional dependencies
__all__ = [
    "SecretManager",
    "Logger",
]

# Try to import each service, but don't fail if dependencies are missing
try:
    from .GoogleSheets import GoogleSheets
    __all__.append("GoogleSheets")
except ImportError as e:
    import logging
    logging.warning(f"GoogleSheets not available: {e}")

try:
    from .ServiceM8 import ServiceM8
    __all__.append("ServiceM8")
except ImportError as e:
    import logging
    logging.warning(f"ServiceM8 not available: {e}")

try:
    from .dbtAPI import dbtAPI
    __all__.append("dbtAPI")
except ImportError:
    pass

try:
    from .GoogleDrive import GoogleDrive
    __all__.append("GoogleDrive")
except ImportError:
    pass

try:
    from .OpenCX import OpenCX
    __all__.append("OpenCX")
except ImportError:
    pass

try:
    from .Intercom import Intercom
    __all__.append("Intercom")
except ImportError:
    pass

try:
    from .GoogleChat import GoogleChat
    __all__.append("GoogleChat")
except ImportError:
    pass

try:
    from .GoogleBigQuery import GoogleBigQuery
    __all__.append("GoogleBigQuery")
except ImportError:
    pass

try:
    from .HubspotAPI import HubspotAPI, AssociationTypes
    __all__.extend(["HubspotAPI", "AssociationTypes"])
except ImportError:
    pass
