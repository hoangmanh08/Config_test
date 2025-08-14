import os
import json

def merge_json_files(directory, output_file="all.json"):
    """
    Duyệt tất cả các file .json trong thư mục và tạo thành một file .json tổng hợp.

    Parameters:
    - directory: Đường dẫn đến thư mục chứa các file .json.
    - output_file: Tên file kết quả tổng hợp (mặc định là "all.json").
    """
    all_data = {}

    # Duyệt qua tất cả các file trong thư mục
    for filename in os.listdir(directory):
        # Kiểm tra xem file có phải là .json không
        if filename.endswith(".json"):
            file_path = os.path.join(directory, filename)

            # Đọc nội dung file json
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

            # Thêm dữ liệu vào dictionary, key là tên file
            all_data[filename] = data

    # Lưu kết quả tổng hợp vào file output_file
    with open(output_file, 'w', encoding='utf-8') as all_file:
        json.dump(all_data, all_file, ensure_ascii=False, indent=4)

    print(f"Tổng hợp các file .json thành công! Kết quả đã được lưu vào '{output_file}'.")

# Ví dụ gọi hàm
merge_json_files("/workspaces/k8sconfig/test")
