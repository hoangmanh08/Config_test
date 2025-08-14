import time
import hashlib
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess

# Hàm tính toán mã băm (hash) của file Excel
def calculate_file_hash(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

# Lớp xử lý sự kiện khi có sự thay đổi trong thư mục
class ExcelFileChangeHandler(FileSystemEventHandler):
    def __init__(self, file_path, last_hash):
        self.file_path = file_path
        self.last_hash = last_hash

    def on_modified(self, event):
        if event.src_path == self.file_path:
            # Tính lại hash của file và so sánh với hash trước đó
            new_hash = calculate_file_hash(self.file_path)
            if new_hash != self.last_hash:
                print("File Excel đã thay đổi, compare_all.py")
                subprocess.run(["python", "/workspaces/k8sconfig/test/compare_all.py"])  # Chạy file main.py
                self.last_hash = new_hash  # Cập nhật hash mới

# Đường dẫn tới file Excel của bạn
excel_file_path = "/workspaces/k8sconfig/test/Kubernetes_Prameters_Configuration.xlsx"

# Tính toán hash ban đầu của file
initial_hash = calculate_file_hash(excel_file_path)

# Tạo đối tượng handler và observer để theo dõi sự thay đổi
handler = ExcelFileChangeHandler(excel_file_path, initial_hash)
observer = Observer()
observer.schedule(handler, os.path.dirname(excel_file_path), recursive=False)

# Bắt đầu theo dõi sự thay đổi
observer.start()

# Chạy vòng lặp kiểm tra mỗi 5 phút (300 giây)
try:
    while True:
        time.sleep(300)  # Kiểm tra sự thay đổi mỗi 5 phút
        print("Đang kiểm tra lại sự thay đổi trong file Excel...")
        # Nếu bạn cần kiểm tra lại trực tiếp về mã băm sau 5 phút, có thể gọi on_modified trực tiếp ở đây nếu cần
        # Tuy nhiên, hiện tại chương trình sẽ chỉ tiếp tục theo dõi và kiểm tra mỗi lần thay đổi được phát hiện bởi Observer
except KeyboardInterrupt:
    observer.stop()

observer.join()
