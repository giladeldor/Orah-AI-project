import os
import logging

# Centralized logger for the project. Import `logger` from this module.
logger = logging.getLogger("AI_Reviewer")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    # write logs to src/logs/app.log (one level above this common package)
    log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'app.log')
    file_handler = logging.FileHandler(log_file)
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
