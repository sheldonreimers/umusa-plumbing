"""Attachment Sync Module - Syncs ServiceM8 attachments to OneDrive.""".

from .config import Config
from .main import main

__all__ = ["Config", "main"]
