import time
import hashlib
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
import logging
from datetime import datetime, timezone, timedelta

# Thiết lập múi giờ Việt Nam (UTC+7)
vietnam_tz = timezone(timedelta(hours=7))

class VietnamFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, vietnam_tz)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.isoformat()

# ===== Cấu hình ghi log ra cả file và console =====
logger = logging.getLogger("file_monitor")
logger.setLevel(logging.INFO)

formatter = VietnamFormatter('%(asctime)s - %(levelname)s - %(message)s', "%Y-%m-%d %H:%M:%S")

file_handler = logging.FileHandler("file_monitor.log")
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)
# ==================================================

def calculate_file_hash(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

class ExcelFileChangeHandler(FileSystemEventHandler):
    def __init__(self, file_path, last_hash):
        self.file_path = file_path
        self.last_hash = last_hash

    def on_modified(self, event):
        if event.src_path == self.file_path:
            new_hash = calculate_file_hash(self.file_path)
            if new_hash != self.last_hash:
                logger.info("File Excel đã thay đổi, đang chạy compare_all.py")
                subprocess.run(["python", "/workspaces/k8sconfig/test/compare_all.py"])
                self.last_hash = new_hash

excel_file_path = "/workspaces/k8sconfig/test/Kubernetes_Prameters_Configuration.xlsx"
initial_hash = calculate_file_hash(excel_file_path)

handler = ExcelFileChangeHandler(excel_file_path, initial_hash)
observer = Observer()
observer.schedule(handler, os.path.dirname(excel_file_path), recursive=False)
observer.start()

logger.info("Đang theo dõi thay đổi trên file Excel... Nhấn Ctrl+C để dừng.")

try:
    while True:
        pass
        # time.sleep(100)
        # logger.info("Đang kiểm tra lại sự thay đổi trong file Excel...")
except KeyboardInterrupt:
    observer.stop()

    logger.info("Đã dừng chương trình theo dõi.")


observer.join()
