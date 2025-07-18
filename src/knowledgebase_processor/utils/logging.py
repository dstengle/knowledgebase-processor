"""Logging utilities for the Knowledge Base Processor."""

import logging
import sys
from typing import Optional
import json

class JSONFormatter(logging.Formatter):
    """
    Formats log records as JSON strings.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_object = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
            "lineno": record.lineno,
        }
        if record.exc_info:
            log_object["exc_info"] = self.formatException(record.exc_info)
        
        return json.dumps(log_object)

def setup_logging(
    log_level: str = "INFO", 
    log_file: Optional[str] = None,
    log_format: str = "text"
) -> None:
    """Set up logging for the application.
    
    Args:
        log_level: The logging level (default: "INFO")
        log_file: Path to a log file (optional)
        log_format: The logging format ('text' or 'json', default: "text")
    """
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")
    
    # Configure root logger
    root_logger = logging.getLogger()
    
    # Remove any existing handlers
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
        
    root_logger.setLevel(numeric_level)
    
    # Create formatter based on log_format
    if log_format == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Create file handler if log_file is provided
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name.
    
    Args:
        name: The name of the logger
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)