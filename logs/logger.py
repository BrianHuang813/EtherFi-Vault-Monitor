import os
import logging
from logging.handlers import RotatingFileHandler

def setup_logger(name: str, log_dir: str = "./logs") -> logging.Logger:
    """
    設定並返回一個 logger，它會同時將日誌輸出到控制台和指定的日誌檔案。
    """
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if logger.hasHandlers():
        return logger

    log_format = logging.Formatter(
        "%(asctime)s - %(name)s - P%(process)d - %(threadName)s - %(levelname)s - %(message)s"
    )

    # 設定檔案 Handler
    log_file = os.path.join(log_dir, f"{name}.log") 
    file_handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)

    # 設定控制台 Handler
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(log_format)
    logger.addHandler(stream_handler)

    return logger