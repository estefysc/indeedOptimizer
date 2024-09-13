import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logger(name, log_file, level=logging.INFO):
    # Create a 'logs' directory if it doesn't exist
    log_directory = "logs"
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    # Construct the full path for the log file
    full_path = os.path.join(log_directory, log_file)

    # Create a logger with the specified name
    logger = logging.getLogger(name)
    logger.setLevel(level)  # Set the logging level

    # Create a file handler that rotates the log file when it reaches 1MB
    # and keeps up to 5 backup log files
    file_handler = RotatingFileHandler(full_path, maxBytes=1024 * 1024, backupCount=5)
    
    # Create a console handler for outputting logs to the console
    console_handler = logging.StreamHandler()

    # Create a formatter that includes timestamp, logger name, level, and message
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Apply the formatter to both handlers
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add both handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

# Create a single logger for the entire application
# This logger will write to 'scraper_app.log' in the 'logs' directory
app_logger = setup_logger('scraper_app', 'scraper_app.log')