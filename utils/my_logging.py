import logging
import os
import sys

import pendulum
import coloredlogs

class MY_Logger:
    def __init__(self, log_file: str = None, log_level=logging.INFO, detailed_logs=False):
        self.log_file = log_file
        self.log_level = log_level
        self.detailed_logs = detailed_logs
        self.log = logging.getLogger()
        self._configure_logger()

    def _configure_logger(self):
        # Clear existing handlers to avoid duplicate logs
        if self.log.hasHandlers():
            self.log.handlers.clear()

        self.log.setLevel(self.log_level)

        # Choose the logging format based on the detailed_logs flag
        log_format = (
            '%(asctime)s  [%(levelname)s]  [%(module)s.%(name)s.%(funcName)s]:%(lineno)s %(message)s'
            if self.detailed_logs
            else '%(asctime)s  [%(levelname).4s]  %(message)s'
        )

        # Configure coloredlogs
        coloredlogs.install(
            level=self.log_level,
            logger=self.log,
            fmt=log_format,
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Add handlers based on whether a log file is provided
        if self.log_file:
            self.log.addHandler(self._get_file_handler())

    def _get_file_handler(self):
        """Create and return a file handler for logging to a file."""
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s | %(levelname).4s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        return file_handler

    def get_logger(self):
        return self.log


# Usage
if __name__ == "__main__":
    # Get current date
    now = pendulum.now().format('YYYY-MM-DD')

    # Set up logging
    directory_name = os.path.basename(os.getcwd())
    log_file = os.path.join(os.getcwd(), f"{directory_name}.log")
    log = MY_Logger(log_file=None, log_level=logging.DEBUG, detailed_logs=False).get_logger()

    log.debug('Testing debug logging')
    log.info(f"Test info: {now}")
    log.warning('Testing logging to console only')
    log.error('Testing error logging')
    log.critical('Testing critical logging')
