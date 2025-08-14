import pandas as pd
import yaml
import tomlkit  
import toml
import re
import json
import os
import configparser
from deepdiff import DeepDiff
import shutil

def find_file_in_directory(directory, file_name):
    # Duyệt qua tất cả các file trong thư mục
    for filename in os.listdir(directory):
        # Kiểm tra nếu tên file khớp với file_name
        if filename == file_name:
            # Trả về đường dẫn đầy đủ của file
            return os.path.join(directory, filename)
    
    # Nếu không tìm thấy file, trả về None
    return None


def compare_toml(excel_file, tom_file, sheet_name, file1, folder_name_NEW, folder_compare):
    def convert_excel_to_toml(excel_file, sheet_name):
        df = pd.read_excel(excel_file, sheet_name=sheet_name)

        yaml_dict = {}
        
        for _, row in df.iterrows():
            keys = row["Parameter"].split(".")
            value = row["Setup Value"]

            flag = False

            # Chuyển đổi giá trị thành kiểu phù hợp  
            if pd.isna(value):  # Kiểm tra nếu value là NaN (trống)  
                value = ""  # Gán None vào value thay vì bỏ qua  
            elif isinstance(value, str) and value.upper() == "TRUE":  
                value = True  
            elif isinstance(value, str) and value.upper() == "FALSE":  
                value = False  
            elif isinstance(value, str) and value == '[]':
                value = []
            elif isinstance(value, float) and value.is_integer():  
                value = int(value)  
            

            
            temp = yaml_dict
            
            
            for key in keys[:-1]:
                if key == "io" and keys[keys.index(key)-1] == "timeouts" :
                    
                    index = keys.index(key)  
                    spec = '.'.join(keys[index:])
                    # spec = \" + spec + \"
                    # last_key = row["Parameter"]  
                    temp[spec] = value
                    flag = True
                    break 

                if "[" in key and "]" in key: 
                    base_key, index = key.split("[")
                    index = int(index.rstrip("]"))
                    temp = temp.setdefault(base_key, [])
                    while len(temp) <= index:
                        temp.append({})
                    temp = temp[index]
                else:
                    temp = temp.setdefault(key, {})

            if flag:
                continue

            last_key = keys[-1]
            if "[" in last_key and "]" in last_key: 
                base_key, index = last_key.split("[")
                index = int(index.rstrip("]"))
                temp = temp.setdefault(base_key, [])
                while len(temp) <= index:
                    temp.append(None)
                temp[index] = value
            else:
                temp[last_key] = value


        # Thay vì ghi vào file, ta trả về chuỗi YAML
        return yaml.dump(yaml_dict, default_flow_style=False, sort_keys=False)

    # Chuyển đổi thành định dạng YAML (không ghi vào file)
    yaml_content = convert_excel_to_toml(excel_file, sheet_name)



    # Hàm chuyển đổi file YAML sang TOML  
    def yaml_to_toml(yaml_content):  
        # Chuyển đổi chuỗi YAML thành dữ liệu Python
        yaml_data = yaml.safe_load(yaml_content)

        # Tạo một tài liệu TOML mới  
        toml_data = tomlkit.document()  

        # Đưa dữ liệu từ YAML vào TOML đồng thời giữ nguyên thứ tự  
        for key, value in yaml_data.items():  
            toml_data[key] = value  

        # Tạo chuỗi TOML từ tài liệu TOML
        toml_output = tomlkit.dumps(toml_data)

        # Thêm lùi đầu dòng cho mỗi dòng giá trị trong bản thân chuỗi đầu ra  
        # Mỗi dòng sẽ là một phần tử trong danh sách lines
        lines = toml_output.splitlines()  
        for i in range(len(lines)):  

            flag = False

            #Kiểm tra xem dòng có dạng '[  ]'
            if lines[i].startswith("[[") and "]]" in lines[i]:
                flag = True
                #Tìm vị trí dấu chấm đầu tiên
                start_idx = lines[i].find(".")
                # Nếu có một dấu chấm và nó không phải là ký tự cuối cùng
                if start_idx != -1 and start_idx < len(lines[i]) - 1:
                    # Thêm dấu ngoặc kép sau dấu chấm đầu tiên
                    first_part = lines[i][:start_idx + 1]
                    rest_part = lines[i][start_idx + 1:]
                    
                    # Tìm vị trí của '.cri' hoặc '.v1.cri'
                    cri_idx2 = rest_part.find('.local')
                    
                    if cri_idx2 != -1 and cri_idx2 + 6 < len(rest_part):
                        # Chèn ngoặc kép sau 'cri'
                        before_cri = rest_part[:cri_idx2 + 6]  # Bao gồm '.cri'
                        after_cri = rest_part[cri_idx2 + 6:]   # Phần còn lại sau '.cri'
                        lines[i] = first_part + '"' + before_cri + '"' + after_cri

            if flag:
                if '=' in lines[i]:  # chỉ lùi những dòng có hình dạng key=value  
                    lines[i] = '  ' + lines[i]  
                continue


            #Kiểm tra xem dòng có dạng '[  ]'
            if lines[i].startswith("[") and "]" in lines[i]:
                #Tìm vị trí dấu chấm đầu tiên
                start_idx = lines[i].find(".")
                # Nếu có một dấu chấm và nó không phải là ký tự cuối cùng
                if start_idx != -1 and start_idx < len(lines[i]) - 1:
                    # Thêm dấu ngoặc kép sau dấu chấm đầu tiên
                    first_part = lines[i][:start_idx + 1]
                    rest_part = lines[i][start_idx + 1:]
                    
                    # Tìm vị trí của '.cri' hoặc '.v1.cri'
                    cri_idx = rest_part.find('.cri')
                    cri_idx1 = rest_part.find(']')
                    
                    if cri_idx != -1 and cri_idx + 4 < len(rest_part):
                        # Chèn ngoặc kép sau 'cri'
                        before_cri = rest_part[:cri_idx + 4]  # Bao gồm '.cri'
                        after_cri = rest_part[cri_idx + 4:]   # Phần còn lại sau '.cri'
                        lines[i] = first_part + '"' + before_cri + '"' + after_cri
                    else:
                        # Chèn ngoặc kép sau 'cri'
                        before_cri1 = rest_part[:cri_idx1]  
                        lines[i] = first_part + '"' + before_cri1 + '"' + ']'

                        # # Nếu không tìm thấy '.cri', chỉ thêm dấu ngoặc kép sau dấu chấm đầu tiên
                        # lines[i] = first_part + '"' + rest_part + '"'

            if '=' in lines[i]:  # chỉ lùi những dòng có hình dạng key=value  
                lines[i] = '  ' + lines[i]  

        # Trả về chuỗi TOML đã chỉnh sửa
        return "\n".join(lines)
        
    # Thực hiện chuyển đổi và lấy chuỗi TOML
    toml_content = yaml_to_toml(yaml_content)



    def transform_toml_content(toml_content):
        lines = toml_content.splitlines()
        transformed_lines = []
        plugins_section_added = False
        stream_processors_section_added = False
        
        for line in lines:
            
            # Thêm phần [plugins] nếu chưa có và gặp dòng [plugins. đầu tiên
            if line.startswith('[plugins.') and not plugins_section_added:
                transformed_lines.append('[plugins]\n')
                plugins_section_added = True
            elif line.startswith('[stream_processors.') and not stream_processors_section_added:
                transformed_lines.append('[stream_processors]\n')
                stream_processors_section_added = True

            
            
            # Thêm dòng vào danh sách kết quả
            transformed_lines.append(line)
        
        # Kết hợp các dòng trở lại thành một chuỗi
        return '\n'.join(transformed_lines)


    # Chuyển đổi nội dung TOML
    transformed_content = transform_toml_content(toml_content)   





    def split_str(input_str):
        # Bước 1: Loại bỏ dấu [ và ]  
        cleaned_str = input_str.strip("[]")  

        # Bước 2: Tách chuỗi bởi dấu "  
        parts = cleaned_str.split('"')  

        # Bước 3: Xử lý và tạo danh sách kết quả  
        result = []  

        for i, part in enumerate(parts):  
            if i % 2 == 0:  # Phần bên ngoài dấu "  
                sub_parts = part.split('.')  
                result.extend([sub_part for sub_part in sub_parts if sub_part])  # Thêm các phần không rỗng  
            else:  # Phần nằm trong dấu "  
                result.append(part)  # Thêm phần nằm giữa dấu "  

        # Bước 4: Kết hợp các phần bên trong  
        if len(result) > 1:  
            # Kết hợp tất cả các phần nằm trong dấu "  
            combined_inner = '.'.join(result[1:2])  # Chỉ cần phần nằm trong dấu "  
            result = [result[0], combined_inner] + result[2:]  # Thay thế và giữ lại các phần còn lại  

        # In kết quả  
        return result

    def same(all_values, i):
        # Kiểm tra số lượng giá trị giống nhau giữa các danh sách liên tiếp  
        current_list = all_values[i]  
        next_list = all_values[i - 1]  

        # Tìm các giá trị giống nhau  
        common_values = set(current_list) & set(next_list)  

        # In kết quả  
        # # print(f"Các giá trị giống nhau giữa danh sách {i} và danh sách {i + 1}: {common_values}")  
        # print(f"Số lượng giá trị giống nhau giữa danh sách {i} và danh sách {i - 1}: {len(common_values)}")  
        return len(common_values)

    def count_same(all_values, i):
        # Chọn danh sách hiện tại (có thể thay đổi chỉ số)  
        current_list = all_values[i]  # Ví dụ: chọn danh sách a  
        # print(f"\nDanh sách hiện tại: {current_list}")  

        # Biến để theo dõi số lượng lớn nhất  
        max_common_count = 0  

        # Kiểm tra số lượng giá trị giống nhau  
        for i, other_list in enumerate(all_values):  
            if other_list is not current_list:  # Chỉ so sánh với danh sách khác  
                # Tìm các giá trị giống nhau  
                common_values = set(current_list) & set(other_list)  
                common_count = len(common_values)  # Đếm số giá trị giống nhau  

                # Cập nhật số lượng lớn nhất nếu cần  
                if common_count > max_common_count:  
                    max_common_count = common_count  

        # # In ra số lượng giá trị giống nhau lớn nhất  
        # print(f"Số lượng giá trị giống nhau lớn nhất giữa danh sách hiện tại và các danh sách khác: {max_common_count}")  
        return max_common_count

    def format_toml(input_content):
        lines = input_content.splitlines()  # Tách chuỗi thành các dòng

        result = []
        indent_level = 0
        # prev_section = ""
        nhay = []
        flag = True

        for line in lines:
            stripped_line = line.strip()

            if stripped_line.startswith("[") and stripped_line.endswith("]"):
                flag = False
            if flag:
                result.append(stripped_line)
                continue

            if stripped_line.startswith("[") and stripped_line.endswith("]"):
                # flag = False
                nhay.append(split_str(stripped_line))

                if len(nhay) == 1:
                    result.append(stripped_line)
                    continue


                indent_level = same(nhay, len(nhay)-1)

                
                indent = "  " * indent_level
                result.append(indent + stripped_line)
            else:
                # Câu lệnh hoặc comment giữ nguyên nhưng được thụt lề theo indent_level
                indent = "  " * (indent_level + 1)
                result.append(indent + stripped_line)

        # Trả về kết quả dưới dạng chuỗi
        return "\n".join(result)

    # Chuyển đổi nội dung
    formatted_content = format_toml(transformed_content)

    output_file = formatted_content

    # # In kết quả đã chuyển đổi ra file
    # output_file = "new_config.toml"  # Định nghĩa tên file đầu ra

    # with open(output_file, "w", encoding="utf-8") as f:
    #     f.write(formatted_content)

    # # In kết quả đã chuyển đổi ra màn hình
    # print(formatted_content)

    # Đọc file TOML và chuyển thành dictionary
    def load_toml(file_path):
        return toml.load(file_path)

    # So sánh hai dictionary và trả về sự khác biệt dưới dạng JSON
    def compare_dicts(dict1, dict2):
        diff = DeepDiff(dict1, dict2, ignore_order=True)
        
        result = {}

        if not diff:
            result["message"] = "Same"
        else:
            result["message"] = "Different"
            
            # Nếu có sự thay đổi giá trị
            if 'values_changed' in diff:
                result["values_changed"] = []
                for key, change in diff['values_changed'].items():
                    result["values_changed"].append({
                        "key": key,
                        "old_value": change['old_value'],
                        "new_value": change['new_value']
                    })

            # Nếu có mục được thêm vào
            if 'dictionary_item_added' in diff:
                result["dictionary_item_added"] = []
                for key in diff['dictionary_item_added']:
                    result["dictionary_item_added"].append({
                        "key": key,
                        # "added_in": "file 2"
                    })

            # Nếu có mục bị xóa
            if 'dictionary_item_removed' in diff:
                result["dictionary_item_removed"] = []
                for key in diff['dictionary_item_removed']:
                    result["dictionary_item_removed"].append({
                        "key": key,
                        # "removed_in": "file 2"
                    })

        return result

    # outputtom_file = sheet_name + "_to_tom.toml"

    # Đảm bảo rằng thư mục 'new_json' tồn tại
    os.makedirs(folder_name_NEW, exist_ok=True)

    # Đường dẫn đến file mới trong thư mục 'new_json'
    tom_file = os.path.join(folder_name_NEW, tom_file)

    with open(tom_file, "w", encoding="utf-8") as f:
        f.write(output_file)

    # Đọc hai file TOML
    # file1 = '/workspaces/k8sconfig/edit_tom/config.toml'
    # file2 = 'new_config.toml'

    file2 = tom_file

    data1 = load_toml(file1)
    data2 = load_toml(file2)

    # So sánh hai dictionary và lấy kết quả
    diff_result = compare_dicts(data1, data2)

    # Đảm bảo rằng thư mục 'new_json' tồn tại
    os.makedirs(folder_compare, exist_ok=True)

    # Đường dẫn đến file mới trong thư mục 'new_json'
    json_file_path = os.path.join(folder_compare, sheet_name + "_compare.json")

    # # Lưu kết quả vào file JSON
    # with open(sheet_name + "_compare.json", 'w') as json_file:
    #     json.dump(diff_result, json_file, indent=4)

    # Lưu kết quả vào file JSON
    with open(json_file_path, 'w') as f:
        json.dump(diff_result, f, indent=4)



def compare_yaml(excel_file, yaml_file, sheet_name, file1, folder_name_NEW, folder_compare):
    def convert_excel_to_yaml(excel_file, yaml_file, sheet_name, folder_name_NEW):
        df = pd.read_excel(excel_file, sheet_name=sheet_name)

        yaml_dict = {}
        
        for _, row in df.iterrows():
            keys = row["Parameter"].split(".")
            value = row["Setup Value"]

            flag = False

            # # Chuyển đổi giá trị thành kiểu phù hợp  
            # if pd.isna(value):  # Kiểm tra nếu value là NaN (trống)  
            #     value = None  # Gán None vào value thay vì bỏ qua 
            # elif value == 0:
            #     value = int(0) 
            # elif isinstance(value, str) and value.upper() == "TRUE":  
            #     value = True  
            # elif isinstance(value, str) and value.upper() == "FALSE":  
            #     value = False  
            # elif value == {}:  # Kiểm tra nếu value là từ điển rỗng
            #     pass  # Giữ nguyên, không thay đổi
            # elif value == "":  # Kiểm tra nếu value là chuỗi rỗng
            #     pass  # Giữ nguyên, không thay đổi
            # elif isinstance(value, float) and value.is_integer():  
            #     value = int(value) 

            if pd.isna(value):
                value = None  

            elif isinstance(value, int) and value == 0:  
                value = int(0)
            
            elif isinstance(value, str) and value.upper() == "TRUE":
                value = "true"
            elif isinstance(value, str) and value.upper() == "FALSE":
                value = "false"
            elif value == {}:  # Kiểm tra nếu value là từ điển rỗng
                pass  # Giữ nguyên, không thay đổi
            elif value == "":  # Kiểm tra nếu value là chuỗi rỗng
                pass  # Giữ nguyên, không thay đổi
            elif isinstance(value, float) and value.is_integer():
                value = int(value)
            
            temp = yaml_dict
                      
            for key in keys[:-1]:
                if key == "kubeadm":
                    index = keys.index(key)  
                    spec = '.'.join(keys[index:])
                    # last_key = row["Parameter"]  
                    temp[spec] = value
                    flag = True
                    break 

                if "[" in key and "]" in key: 
                    base_key, index = key.split("[")
                    index = int(index.rstrip("]"))
                    temp = temp.setdefault(base_key, [])
                    while len(temp) <= index:
                        temp.append({})
                    temp = temp[index]
                else:
                    temp = temp.setdefault(key, {})

            if flag:
                continue

            last_key = keys[-1]
            if "[" in last_key and "]" in last_key: 
                base_key, index = last_key.split("[")
                index = int(index.rstrip("]"))
                temp = temp.setdefault(base_key, [])
                while len(temp) <= index:
                    temp.append(None)
                temp[index] = value
            else:
                temp[last_key] = value

        # Đảm bảo rằng thư mục 'new_json' tồn tại
        os.makedirs(folder_name_NEW, exist_ok=True)

        # Đường dẫn đến file mới trong thư mục 'new_json'
        yaml_file = os.path.join(folder_name_NEW, yaml_file)


        with open(yaml_file, "w") as f:
            yaml.dump(yaml_dict, f, default_flow_style=False, sort_keys=False)

        # print(f"Done!")

    # if __name__ == "__main__":
    #     input_excel = "etcd.xlsx" 
    #     output_yaml = "output.yaml"  
    convert_excel_to_yaml(excel_file, yaml_file, sheet_name, folder_name_NEW)   

    def process_yaml_file(yaml_file):
        # Read the file and process lines
        with open(yaml_file, 'r') as file:
            lines = file.readlines()
        
        # Process each line
        processed_lines = []
        for line in lines:
            # Replace '{}' with an actual empty dict
            if "'{}'" in line:
                line = line.replace("'{}'", "{}")
            
            # Replace '""' with an actual empty string
            if "'\"\"'" in line:
                line = line.replace("'\"\"'", '""')

            # Replace '"0"' with "0"
            if "'\"0\"'" in line:
                line = line.replace("'\"0\"'", '"0"')

            if "'true'" in line:
                line = line.replace("'true'", "true")

            if "'false'" in line:
                line = line.replace("'false'", "false")
            
            processed_lines.append(line)
        
        # Write processed lines to output file
        with open(yaml_file, 'w') as file:
            file.writelines(processed_lines)
        
        # print(f"Processed file saved to {output_file}")

    # Example usage
    # input_file = 'b.yaml'
    # output_file = 'b_processed.yaml'
    process_yaml_file(yaml_file)

    

    # Đọc file TOML và chuyển thành dictionary
    def load_yaml(file_path):
        with open(file_path, 'r') as file:
            return yaml.load(file, Loader=yaml.SafeLoader)


    # So sánh hai dictionary và trả về sự khác biệt dưới dạng JSON
    def compare_dicts(dict1, dict2):
        diff = DeepDiff(dict1, dict2, ignore_order=True)
        
        result = {}

        if not diff:
            result["message"] = "Same"
        else:
            result["message"] = "Different"
            
            # Nếu có sự thay đổi giá trị
            if 'values_changed' in diff:
                result["values_changed"] = []
                for key, change in diff['values_changed'].items():
                    result["values_changed"].append({
                        "key": key,
                        "old_value": change['old_value'],
                        "new_value": change['new_value']
                    })

            # Nếu có mục được thêm vào
            if 'dictionary_item_added' in diff:
                result["dictionary_item_added"] = []
                for key in diff['dictionary_item_added']:
                    result["dictionary_item_added"].append({
                        "key": key,
                        # "added_in": "file 2"
                    })

            # Nếu có mục bị xóa
            if 'dictionary_item_removed' in diff:
                result["dictionary_item_removed"] = []
                for key in diff['dictionary_item_removed']:
                    result["dictionary_item_removed"].append({
                        "key": key,
                        # "removed_in": "file 2"
                    })

        return result

    # Đọc hai file TOML
    # file1 = '/workspaces/k8sconfig/default/config.yaml'
    file2 = yaml_file

    data1 = load_yaml(file1)
    data2 = load_yaml(file2)

    # So sánh hai dictionary và lấy kết quả
    diff_result = compare_dicts(data1, data2)

    # Đảm bảo rằng thư mục 'new_json' tồn tại
    os.makedirs(folder_compare, exist_ok=True)

    # Đường dẫn đến file mới trong thư mục 'new_json'
    json_file_path = os.path.join(folder_compare, sheet_name + "_compare.json")


    # Lưu kết quả vào file JSON
    with open(json_file_path, 'w') as f:
        json.dump(diff_result, f, indent=4)


def compare_conf(excel_file, conf_file, sheet_name, file1, folder_name_NEW, folder_compare):
    def excel_to_conf(excel_file, conf_file, sheet_name, folder_name_NEW):
        # Đọc dữ liệu từ file Excel (giả sử có 2 cột: key và value)
        df = pd.read_excel(excel_file, sheet_name=sheet_name)

        # Đảm bảo rằng thư mục 'new_json' tồn tại
        os.makedirs(folder_name_NEW, exist_ok=True)

        # Đường dẫn đến file mới trong thư mục 'new_json'
        conf_file = os.path.join(folder_name_NEW, conf_file)

        # Mở file .conf để ghi dữ liệu
        with open(conf_file, 'w') as conf:
            # Duyệt qua từng dòng của DataFrame
            for index, row in df.iterrows():
                key = row['Parameter']   # Cột key trong file Excel
                value = row['Setup Value']  # Cột value trong file Excel
                conf.write(f"{key}={value}\n")
    excel_to_conf(excel_file, conf_file, sheet_name, folder_name_NEW)

    # Đọc file .conf và chuyển thành dictionary
    def load_conf(file_path):
        config = configparser.ConfigParser()
        
        # Đọc nội dung file .conf
        with open(file_path, 'r') as file:
            content = file.read()
        
        # Thêm một section giả (section 'default') nếu file không có section header
        if not content.startswith('['):
            content = '[default]\n' + content
        
        # Ghi nội dung có section header vào file tạm thời
        with open('temp.conf', 'w') as temp_file:
            temp_file.write(content)
        
        # Đọc file tạm thời và chuyển thành dictionary
        config.read('temp.conf')
        config_dict = {section: dict(config.items(section)) for section in config.sections()}
        
        return config_dict

    # So sánh hai dictionary và trả về sự khác biệt dưới dạng JSON
    def compare_dic(dict1, dict2):
        diff = DeepDiff(dict1, dict2, ignore_order=True)
        
        result = {}

        if not diff:
            result["message"] = "Same"
        else:
            result["message"] = "Different"
            
            # Nếu có sự thay đổi giá trị
            if 'values_changed' in diff:
                result["values_changed"] = []
                for key, change in diff['values_changed'].items():
                    result["values_changed"].append({
                        "key": key,
                        "old_value": change['old_value'],
                        "new_value": change['new_value']
                    })

            # Nếu có mục được thêm vào
            if 'dictionary_item_added' in diff:
                result["dictionary_item_added"] = []
                for key in diff['dictionary_item_added']:
                    result["dictionary_item_added"].append({
                        "key": key,
                        # "added_in": "file 2"
                    })

            # Nếu có mục bị xóa
            if 'dictionary_item_removed' in diff:
                result["dictionary_item_removed"] = []
                for key in diff['dictionary_item_removed']:
                    result["dictionary_item_removed"].append({
                        "key": key,
                        # "removed_in": "file 2"
                    })

        return result

    # Đọc hai file .conf
    # file1 = '/workspaces/k8sconfig/edit_tom/sysctl.conf'
    file2 = conf_file

    data1 = load_conf(file1)
    data2 = load_conf(file2)

    # So sánh hai dictionary và lấy kết quả
    diff_result = compare_dic(data1, data2)

    # Đảm bảo rằng thư mục 'new_json' tồn tại
    os.makedirs(folder_compare, exist_ok=True)

    # Đường dẫn đến file mới trong thư mục 'new_json'
    json_file_path = os.path.join(folder_compare, sheet_name + "_compare.json")

    # Lưu kết quả vào file JSON
    with open(json_file_path, 'w') as f:
        json.dump(diff_result, f, indent=4)

    # # Lưu kết quả vào file JSON
    # with open('diff_result_conf.json', 'w') as json_file:
    #     json.dump(diff_result, json_file, indent=4)

    # print("File diff_result.json đã được lưu.")


def compare_10_kubeadm(excel_file, conf_file, sheet_name, file1, folder_name_NEW, folder_compare):
    def excel_10_to_conf(excel_file, conf_file, sheet_name, folder_name_NEW):
        # Đọc dữ liệu từ file Excel (giả sử có 2 cột: key và value)
        df = pd.read_excel(excel_file, sheet_name=sheet_name)

        # Đảm bảo rằng thư mục 'new_json' tồn tại
        os.makedirs(folder_name_NEW, exist_ok=True)

        # Đường dẫn đến file mới trong thư mục 'new_json'
        conf_file = os.path.join(folder_name_NEW, conf_file)

        # Mở file .conf để ghi dữ liệu
        with open(conf_file, 'w') as conf:
            conf.write(f"{'[Service]'}\n")
            # Duyệt qua từng dòng của DataFrame
            for index, row in df.iterrows():
                key = row['Parameter']   # Cột key trong file Excel
                value = row['Setup Value']  # Cột value trong file Excel
                if pd.isna(value):  # Kiểm tra nếu value là NaN (trống)  
                    value = ""  # Gán None vào value thay vì bỏ qua 
                conf.write(f"{key}={value}\n")
    excel_10_to_conf(excel_file, conf_file,sheet_name, folder_name_NEW)
    
    
    def clean_conf_file(conf_file):
        """Đọc file và loại bỏ các dòng comment và khoảng trắng."""
        with open(conf_file, 'r') as f:
            lines = f.readlines()

        cleaned_lines = []
        for line in lines:
            # Bỏ qua các dòng comment (bắt đầu bằng #) và các dòng trống
            if line.strip() and not line.strip().startswith('#'):
                cleaned_lines.append(line.strip())

        return "\n".join(cleaned_lines)

    def compare_10_conf_files(file1, conf_file):
        result = {}

        # Làm sạch các file bằng cách loại bỏ comment và dòng trống
        conf1 = clean_conf_file(file1)
        conf2 = clean_conf_file(file2)

        # So sánh hai file đã làm sạch
        diff = DeepDiff(conf1, conf2)

        # Nếu không có sự khác biệt
        if not diff:
            result["message"] = "Same"
        else:
            result["message"] = "Different"
            
            # Nếu có sự thay đổi giá trị
            if 'values_changed' in diff:
                result["values_changed"] = []
                for key, change in diff['values_changed'].items():
                    result["values_changed"].append({
                        "key": key,
                        "old_value": change['old_value'],
                        "new_value": change['new_value']
                    })

            # Nếu có mục được thêm vào
            if 'dictionary_item_added' in diff:
                result["dictionary_item_added"] = []
                for key in diff['dictionary_item_added']:
                    result["dictionary_item_added"].append({
                        "key": key,
                    })

            # Nếu có mục bị xóa
            if 'dictionary_item_removed' in diff:
                result["dictionary_item_removed"] = []
                for key in diff['dictionary_item_removed']:
                    result["dictionary_item_removed"].append({
                        "key": key,
                    })

        return result

    # Đường dẫn đến các file .conf
    # file1 = '/workspaces/test/10cu/10-kubeadm.conf'
    file2 = conf_file

    # So sánh và in kết quả
    diff_result = compare_10_conf_files(file1, file2)

    # Đảm bảo rằng thư mục 'new_json' tồn tại
    os.makedirs(folder_compare, exist_ok=True)

    # Đường dẫn đến file mới trong thư mục 'new_json'
    json_file_path = os.path.join(folder_compare, sheet_name + "_compare.json")

    # Lưu kết quả vào file JSON
    with open(json_file_path, 'w') as f:
        json.dump(diff_result, f, indent=4)


def compare_containerd_service(excel_file, conf_file, sheet_name, file1, folder_name_NEW, folder_compare):
    def convert_excel_to_yaml(excel_file, sheet_name):
        df = pd.read_excel(excel_file, sheet_name=sheet_name)

        yaml_dict = {}
        
        for _, row in df.iterrows():
            keys = row["Parameter"].split(".")
            value = row["Setup Value"]

            flag = False

            if pd.isna(value):  # Kiểm tra nếu value là NaN (trống)  
                value = None  # Gán None vào value thay vì bỏ qua  
            elif isinstance(value, str) and value.upper() == "TRUE":  
                value = True  
            elif isinstance(value, str) and value.upper() == "FALSE":  
                value = False  
            elif value == {}:  # Kiểm tra nếu value là từ điển rỗng
                pass  # Giữ nguyên, không thay đổi
            elif value == "":  # Kiểm tra nếu value là chuỗi rỗng
                pass  # Giữ nguyên, không thay đổi
            elif isinstance(value, float) and value.is_integer():  
                value = int(value)
            


            temp = yaml_dict
        
            for key in keys[:-1]:
                if key == "kubeadm":
                    index = keys.index(key)  
                    spec = '.'.join(keys[index:])
                    # last_key = row["Parameter"]  
                    temp[spec] = value
                    flag = True
                    break 

                if "[" in key and "]" in key: 
                    base_key, index = key.split("[")
                    index = int(index.rstrip("]"))
                    temp = temp.setdefault(base_key, [])
                    while len(temp) <= index:
                        temp.append({})
                    temp = temp[index]
                else:
                    temp = temp.setdefault(key, {})

            if flag:
                continue

            last_key = keys[-1]
            if "[" in last_key and "]" in last_key: 
                base_key, index = last_key.split("[")
                index = int(index.rstrip("]"))
                temp = temp.setdefault(base_key, [])
                while len(temp) <= index:
                    temp.append(None)
                temp[index] = value
            else:
                temp[last_key] = value

        # Chuyển nội dung YAML vào một biến (string)
        # yaml_file = yaml.dump(yaml_dict, default_flow_style=False, sort_keys=False)

        # # Lưu nội dung YAML vào file
        # with open(yaml_file, "w") as f:
        #     yaml.dump(yaml_dict, f, default_flow_style=False, sort_keys=False)

        return yaml.dump(yaml_dict, default_flow_style=False, sort_keys=False)


    yaml1_file = convert_excel_to_yaml(excel_file, sheet_name)

    def convert_yaml_to_service(yaml1_file, conf_file, folder_name_NEW):
        # with open(yaml1_file, 'r') as f:
        #     yaml_data = yaml.safe_load(f)
        yaml_data = yaml.safe_load(yaml1_file)

        # Đảm bảo rằng thư mục 'new_json' tồn tại
        os.makedirs(folder_name_NEW, exist_ok=True)

        # Đường dẫn đến file mới trong thư mục 'new_json'
        conf_file = os.path.join(folder_name_NEW, conf_file)
        
        with open(conf_file, 'w') as f:
            # Write [Unit] section
            f.write("[Unit]\n")
            for key, value in yaml_data.get('Unit', {}).items():
                f.write(f"{key}={value}\n")
            
            # Write [Service] section
            f.write("\n[Service]\n")
            for key, value in yaml_data.get('Service', {}).items():
                f.write(f"{key}={value}\n")

            f.write("\n[Install]\n")
            for key, value in yaml_data.get('Install', {}).items():
                f.write(f"{key}={value}\n")

    # Usage example
    convert_yaml_to_service(yaml1_file, conf_file, folder_name_NEW)

    def clean_service_file(file_path):
        """Đọc file .service và loại bỏ các dòng comment và khoảng trắng."""
        with open(file_path, 'r') as f:
            lines = f.readlines()

        cleaned_lines = []
        for line in lines:
            # Bỏ qua các dòng comment (bắt đầu bằng #) và các dòng trống
            if line.strip() and not line.strip().startswith('#'):
                cleaned_lines.append(line.strip())

        return "\n".join(cleaned_lines)

    def compare_contained_files(file1, conf_file):
        result = {}

        # Làm sạch các file bằng cách loại bỏ comment và dòng trống
        service1 = clean_service_file(file1)
        service2 = clean_service_file(file2)

        # So sánh hai file đã làm sạch
        diff = DeepDiff(service1, service2)

        # Nếu không có sự khác biệt
        if not diff:
            result["message"] = "Same"
        else:
            result["message"] = "Different"
            
            # Nếu có sự thay đổi giá trị
            if 'values_changed' in diff:
                result["values_changed"] = []
                for key, change in diff['values_changed'].items():
                    result["values_changed"].append({
                        "key": key,
                        "old_value": change['old_value'],
                        "new_value": change['new_value']
                    })

            # Nếu có mục được thêm vào
            if 'dictionary_item_added' in diff:
                result["dictionary_item_added"] = []
                for key in diff['dictionary_item_added']:
                    result["dictionary_item_added"].append({
                        "key": key,
                    })

            # Nếu có mục bị xóa
            if 'dictionary_item_removed' in diff:
                result["dictionary_item_removed"] = []
                for key in diff['dictionary_item_removed']:
                    result["dictionary_item_removed"].append({
                        "key": key,
                    })

        return result  # Trả về đối tượng Python, không phải chuỗi JSON

    # Đường dẫn đến các file .service
    # file1 = '/workspaces/test/containerd.service'
    file2 = conf_file

    # So sánh và lưu kết quả vào file JSON
    result1 = compare_contained_files(file1, file2)

    # Đảm bảo rằng thư mục 'new_json' tồn tại
    os.makedirs(folder_compare, exist_ok=True)

    # Đường dẫn đến file mới trong thư mục 'new_json'
    json_file_path = os.path.join(folder_compare, sheet_name + "_compare.json")

    # Lưu kết quả vào file JSON
    with open(json_file_path, 'w') as f:
        json.dump(result1, f, indent=4)




def process_excel(file_path):
    # Đọc file Excel với nhiều sheet
    xl = pd.ExcelFile(file_path)
    result = {}

    directory_find = '/workspaces/k8sconfig/test/default'

    folder_name_NEW = "/workspaces/k8sconfig/test/new_file_default"
    folder_compare = "/workspaces/k8sconfig/test/compare"

    # Duyệt qua tất cả các sheet
    for sheet_name in xl.sheet_names:
        if '.conf' in sheet_name:
            if sheet_name == "sysctl.conf":
                new_config_file = "/workspaces/k8sconfig/test/new_file_default/new_" + sheet_name
                file1 = find_file_in_directory(directory_find, sheet_name)
                compare_conf(file_path, new_config_file, sheet_name, file1, folder_name_NEW, folder_compare)
            if sheet_name == "10-kubeadm.conf":
                new_config_file = "/workspaces/k8sconfig/test/new_file_default/new_" + sheet_name
                file1 = find_file_in_directory(directory_find, sheet_name)
                compare_10_kubeadm(file_path, new_config_file, sheet_name, file1, folder_name_NEW, folder_compare)
        elif '.toml' in sheet_name:
            if sheet_name == "config.toml":
                new_config_file = "/workspaces/k8sconfig/test/new_file_default/new_" + sheet_name
                file1 = find_file_in_directory(directory_find, sheet_name)
                compare_toml(file_path, new_config_file, sheet_name, file1, folder_name_NEW, folder_compare)
        elif '.yaml' in sheet_name:
            if sheet_name == "config.yaml":
                new_yaml_file = "/workspaces/k8sconfig/test/new_file_default/new_" + sheet_name
                file1 = find_file_in_directory(directory_find, sheet_name)
                compare_yaml(file_path, new_yaml_file, sheet_name, file1, folder_name_NEW, folder_compare)
            if sheet_name == "audit-policy.yaml":
                new_yaml_file = "/workspaces/k8sconfig/test/new_file_default/new_" + sheet_name
                file1 = find_file_in_directory(directory_find, sheet_name)
                compare_yaml(file_path, new_yaml_file, sheet_name, file1, folder_name_NEW, folder_compare)
            if sheet_name == "crictl.yaml":
                new_yaml_file = "/workspaces/k8sconfig/test/new_file_default/new_" + sheet_name
                file1 = find_file_in_directory(directory_find, sheet_name)
                compare_yaml(file_path, new_yaml_file, sheet_name, file1, folder_name_NEW, folder_compare)
            if sheet_name == "etcd.yaml":
                new_yaml_file = "/workspaces/k8sconfig/test/new_file_default/new_" + sheet_name
                file1 = find_file_in_directory(directory_find, sheet_name)
                compare_yaml(file_path, new_yaml_file, sheet_name, file1, folder_name_NEW, folder_compare)
            if sheet_name == "kube-apiserver.yaml":
                new_yaml_file = "/workspaces/k8sconfig/test/new_file_default/new_" + sheet_name
                file1 = find_file_in_directory(directory_find, sheet_name)
                compare_yaml(file_path, new_yaml_file, sheet_name, file1, folder_name_NEW, folder_compare)
            if sheet_name == "kube-controller-manager.yaml":
                new_yaml_file = "/workspaces/k8sconfig/test/new_file_default/new_" + sheet_name
                file1 = find_file_in_directory(directory_find, sheet_name)
                compare_yaml(file_path, new_yaml_file, sheet_name, file1, folder_name_NEW, folder_compare)
            if sheet_name == "kube-scheduler.yaml":
                new_yaml_file = "/workspaces/k8sconfig/test/new_file_default/new_" + sheet_name
                file1 = find_file_in_directory(directory_find, sheet_name)
                compare_yaml(file_path, new_yaml_file, sheet_name, file1, folder_name_NEW, folder_compare)
        elif '.service' in sheet_name:
            if sheet_name == "containerd.service":
                new_yaml_file = "/workspaces/k8sconfig/test/new_file_default/new_" + sheet_name
                file1 = find_file_in_directory(directory_find, sheet_name)
                compare_containerd_service(file_path, new_yaml_file, sheet_name, file1, folder_name_NEW, folder_compare)

        # else:
        #     print(f"Bỏ qua sheet: {sheet_name}")


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

def delete_folder(folder_path):
    # Đường dẫn đến thư mục cần kiểm tra và xóa
    # folder_path = 'path/to/your/folder'

    # Kiểm tra nếu thư mục tồn tại
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        shutil.rmtree(folder_path)
    #     try:
    #         # Xóa thư mục
    #         shutil.rmtree(folder_path)
    #         print(f"Thư mục '{folder_path}' đã được xóa.")
    #     except Exception as e:
    #         print(f"Đã xảy ra lỗi khi xóa thư mục: {e}")
    # else:
    #     print(f"Thư mục '{folder_path}' không tồn tại.")

def delete_file(file_path):
    # # Đường dẫn đến file cần kiểm tra và xóa
    # file_path = 'path/to/your/file.txt'

    # Kiểm tra nếu file tồn tại
    if os.path.exists(file_path) and os.path.isfile(file_path):
        os.remove(file_path)
    #     try:
    #         # Xóa file
    #         os.remove(file_path)
    #         print(f"File '{file_path}' đã được xóa.")
    #     except Exception as e:
    #         print(f"Đã xảy ra lỗi khi xóa file: {e}")
    # else:
    #     print(f"File '{file_path}' không tồn tại.")

def main():
    # compare_toml('/workspaces/k8sconfig/edit_tom/config.xlsx')
    # compare_yaml('/workspaces/k8sconfig/parameterfiles/config.xlsx','to_yam.yaml')
    # compare_conf('/workspaces/k8sconfig/edit_tom/sysctl.xlsx', 'to_sysctl.conf')

    delete_folder('/workspaces/k8sconfig/test/compare')
    delete_folder('/workspaces/k8sconfig/test/new_file_default')
    delete_file('/workspaces/k8sconfig/test/temp.conf')

    process_excel('/workspaces/k8sconfig/test/Kubernetes_Prameters_Configuration.xlsx')

    merge_json_files("/workspaces/k8sconfig/test/compare")

    delete_file('/workspaces/k8sconfig/test/temp.conf')

if __name__ == "__main__":
    main()