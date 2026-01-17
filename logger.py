"""
Shared logging configuration for Bing Wallpaper Downloader
"""
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta

def setup_logger(name: str, log_dir: Path = None, max_age_days: int = 7) -> logging.Logger:
    """
    Set up a logger with file and console handlers
    
    Args:
        name: Logger name (e.g., 'downloader', 'tray')
        log_dir: Directory for log files (default: %APPDATA%/BingWallpaperDownloader/logs)
        max_age_days: Delete logs older than this many days
    
    Returns:
        Configured logger instance
    """
    # Determine log directory
    if log_dir is None:
        appdata = Path.home() / "AppData" / "Roaming" / "BingWallpaperDownloader"
        log_dir = appdata / "logs"
    
    # Create log directory if it doesn't exist
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Clean up old log files
    cleanup_old_logs(log_dir, max_age_days)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Prevent duplicate handlers if logger already exists
    if logger.handlers:
        return logger
    
    # File handler - daily log file
    log_file = log_dir / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # Console handler (only if console is available)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def cleanup_old_logs(log_dir: Path, max_age_days: int):
    """Delete log files older than max_age_days"""
    try:
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        
        for log_file in log_dir.glob("*.log"):
            try:
                # Get file modification time
                file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                
                if file_time < cutoff_date:
                    log_file.unlink()
            except Exception:
                # Ignore errors when deleting individual files
                pass
    except Exception:
        # Ignore errors during cleanup
        pass
