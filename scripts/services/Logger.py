"""Module configuring the project's logger."""

import logging
import sys
from logging.handlers import RotatingFileHandler


class Logger:
    """A reusable Logger class to configure and provide a logger instance."""

    def __init__(
        self,
        name: str,
        log_file: str = "app.log",
        level: int = logging.INFO,
        max_bytes: int = 5 * 1024 * 1024,
        backup_count: int = 5,
    ):
        """
        Initialize the Logger with specified configurations.

        Args:
            name: Name of the logger.
            log_file: File path for the log file.
            level: Logging level (e.g., logging.ERROR, logging.CRITICAL).
            max_bytes: Maximum size in bytes before rotating the log file.
            backup_count: Number of backup log files to keep.
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)  # Set logger's base level

        if not self.logger.handlers:
            formatter = logging.Formatter(
                fmt="%(asctime)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )

            # Console Handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)  # Capture logs at the specified level (INFO)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

            # File Handler
            file_handler = RotatingFileHandler(
                log_file, maxBytes=max_bytes, backupCount=backup_count
            )
            file_handler.setLevel(level)  # Capture logs at the specified level (INFO)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def get_logger(self):
        """
        Return the configured logger instance.

        Returns:
            Logger instance.
        """
        return self.logger
