import dictdiffer
import toml
import yaml
import configparser
import json
from os import listdir
from os.path import isfile, join, isdir


def compare_same_keys(current_file, default_file):
    data1_li = []
    data2_li = []
    with open(current_file, 'r') as rdr:
        for line in rdr:
            if line[0] not in ("#", "["):
                k, v = line.strip().split('=', 1)
                item_dict = {}
                item_dict[k.strip()] = v.strip()
                data1_li.append(item_dict)

    with open(default_file, 'r') as rdr:
        for line in rdr:
            if line[0] not in ("#", "["):
                k, v = line.strip().split('=', 1)
                item_dict = {}
                item_dict[k.strip()] = v.strip()
                data2_li.append(item_dict)
    if len(data1_li) != len(data2_li):
        return data1_li
    dif = []
    for k in range(len(data1_li)):
        # dif_item = list(dictdiffer.diff(data1_li[k], data2_li[k]))
        dif = dif + list(dictdiffer.diff(data1_li[k], data2_li[k]))
        # if dif_item != []:
        #    dif.append(dif_item)
    if dif != []:
        return dif
    return None


def get_dict(x):
    config = configparser.ConfigParser(allow_no_value=False)
    config.read(x)
    sections_dict = {}
    sections_dict.update(config._sections)
    # remove blank sections
    sections_dict = {k: v for k, v in sections_dict.items() if v != {} }

    return sections_dict


def compare_dict(current_file, default_file):
    data1_dict = {}
    data2_dict = {}
    with open(current_file, 'r') as rdr:
        for line in rdr:
            if line.strip():
                if line[0] != "#":
                    k, v = line.strip().split('=', 1)
                    data1_dict[k.strip()] = v.strip()

    with open(default_file, 'r') as rdr:
        for line in rdr:
            if line.strip():
                if line[0] != "#":
                    k, v = line.strip().split('=', 1)
                    data2_dict[k.strip()] = v.strip()

    if data1_dict != data2_dict:
        return list(dictdiffer.diff(data1_dict, data2_dict))
    return None


def compare_set(current_file, default_file):
    with open(current_file, 'r') as rdr:
        data1_set = set(rdr.read().split())

    with open(default_file, 'r') as rdr:
        data2_set = set(rdr.read().split())

    if data1_set != data2_set:
        return list(data1_set.difference(data2_set))
    return None


def compare_toml(current_file, default_file):
    data1_dict = toml.load(current_file, _dict=dict)
    data2_dict = toml.load(default_file, _dict=dict)

    if data1_dict != data2_dict:
        return list(dictdiffer.diff(data1_dict, data2_dict))


# Load YAML file
def load_yaml(file_path):
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)


# Remove ignored keys recursively
def remove_ignored_keys(data, keys_to_ignore):
    if isinstance(data, dict):
        return {
            key: remove_ignored_keys(value, keys_to_ignore)
            for key, value in data.items()
            if key not in keys_to_ignore
        }
    elif isinstance(data, list):
        return [remove_ignored_keys(item, keys_to_ignore) for item in data]
    else:
        return data


# Function to remove specific keys
def filter_keys(data, keys_to_ignore):
    if isinstance(data, dict):
        # Keep only keys that are not in the keys_to_ignore list
        return {
            key: filter_keys(value, keys_to_ignore)
            for key, value in data.items()
            if key not in keys_to_ignore
        }
    elif isinstance(data, list):
        # Recursively filter items in the list
        return [filter_keys(item, keys_to_ignore) for item in data]
    return data  # Return value as is if it's not a list or dict


def remove_strings_starting_with_prefixes(d, prefixes):
    for key, value in d.items():
        if isinstance(value, dict):  # If the value is a dictionary, recurse
            remove_strings_starting_with_prefixes(value, prefixes)
        elif isinstance(value, list):  # If the value is a list, process each item
            for i in range(len(value)):
                if isinstance(value[i], dict):  # If an item in the list is a dictionary, recurse
                    remove_strings_starting_with_prefixes(value[i], prefixes)
                elif isinstance(value[i], str) and any(value[i].startswith(prefix) for prefix in prefixes):
                    # Remove string items starting with any of the prefixes
                    value[i] = None  # Replace with None first for filtering later
            # Remove any None values in the list after processing
            d[key] = [item for item in value if item is not None]
        else:
            # If the value is neither a list nor a dictionary, do nothing
            pass


def compare_yaml(current_file, default_file, ignore_list):
    # Load YAML files
    data1 = load_yaml(current_file)
    data2 = load_yaml(default_file)

    # Remove keys to ignore
    filtered_data1 = remove_ignored_keys(data1, ignore_list)
    filtered_data2 = remove_ignored_keys(data2, ignore_list)

    etcd_comand_prefixes = ['--advertise-client-urls', '--initial-advertise-peer-urls',
                            '--initial-cluster', '--listen-client-urls', '--listen-metrics-urls',
                            '--listen-peer-urls', '--name']  # Example of ignoring multiple prefixes
    kubeapiserver_command_prefixes = ['--advertise-address']

    command_prefixes = etcd_comand_prefixes + kubeapiserver_command_prefixes
    remove_strings_starting_with_prefixes(filtered_data1, command_prefixes)
    remove_strings_starting_with_prefixes(filtered_data2, command_prefixes)

    return list(dictdiffer.diff(filtered_data1, filtered_data2))


def compare_service(file_config_path, file_default_config_path):
    dict_config = get_dict(file_config_path)
    dict_default_config = get_dict(file_default_config_path)

    return list(dictdiffer.diff(dict_config, dict_default_config))


def comparer(config_file, file_config_path, file_default_config_path, ignore_list):
    if config_file == "containerd.conf":
        return compare_set(file_config_path, file_default_config_path)

    elif config_file == "10-kubeadm.conf":
        return compare_same_keys(file_config_path, file_default_config_path)

    else:
        if ".yaml" in config_file:
            return compare_yaml(file_config_path, file_default_config_path, ignore_list)

        elif ".toml" in config_file:
            return compare_toml(file_config_path, file_default_config_path)

        elif ".conf" in config_file:
            return compare_dict(file_config_path, file_default_config_path)

        elif ".service" in config_file:
            return compare_service(file_config_path, file_default_config_path)

        else:
            return None


def extract_list_files(playbook_file):
    with open(playbook_file, 'r') as file:
        playbook_content = yaml.safe_load(file)
    tasks = playbook_content[0]['tasks']
    fetch_tasks = [task for task in tasks if 'fetch' in task]
    return fetch_tasks[0]['with_items']


def check_configs(path_configs, path_default_configs, metric_path, ignore_list):
    result = {}
    types = ["MASTER", "COMP", "DB"]
    file_metric_name = "metrics_changed.prom"
    file_metric_path = join(metric_path, file_metric_name)
    with open(file_metric_path, 'w') as file:
        for type in types:
            path_default = join(path_default_configs, type)
            path_hosts = join(path_configs, type)
            hosts = [f for f in listdir(path_hosts) if isdir(join(path_hosts, f))]
            # get list_files in with_items fetch_xxx.yaml
            if type == "MASTER":
                playbook_file = "/home/vttek/Downloads/saocd/check_config/ansible/fetch_masters.yaml"
            elif type == "DB":
                playbook_file = "/home/vttek/Downloads/saocd/check_config/ansible/fetch_workers_DB.yaml"
            elif type == "COMP":
                playbook_file = "/home/vttek/Downloads/saocd/check_config/ansible/fetch_workers_COMP.yaml"
            config_default_files = extract_list_files(playbook_file)
            result[type] = {}
            result[type]["list_files"] = []
            result[type]["list_files"] = config_default_files
            result[type]["list_servers"] = []

            for host in hosts:
                host_str = {}
                host_str["hostname"] = host
                host_str["result"] = []
                path_host = join(path_hosts, host)
                # result[type]["list_servers"][host] = {}
                config_files = [f for f in listdir(path_host) if isfile(join(path_host, f))]
                for config_file in config_files:
                    file_config_path = join(path_hosts, host, config_file)
                    file_default_config_path = join(path_default, config_file)

                    diff = comparer(config_file, file_config_path, file_default_config_path, ignore_list)

                    # Convert differences to a JSON-compatible format
                    diff_json = []
                    if diff:
                        for change in diff:
                            change_type = change[0]

                            if change_type == 'change':
                                _, key, value = change
                                diff_json.append({
                                    'type': change_type,
                                    'key': key,
                                    'value': value
                                })
                            elif change_type == 'add':
                                _, key, value = change
                                diff_json.append({
                                    'type': change_type,
                                    'key': key,
                                    'value': value
                                })
                            elif change_type == 'remove':
                                _, key, value = change
                                diff_json.append({
                                    'type': change_type,
                                    'key': key,
                                    'value': value
                                })

                    # Convert the differences to JSON
                    # diff_json_str = json.dumps(diff_json)

                    # Convert the differences to JSON
                    # diff_json_str = json.dumps(diff_json, indent=2)
                    metric = "kubernetes_configuration_change{{node=\"{0}\",file=\"{1}\"}} 0".format(host, config_file)
                    if len(diff_json) > 0:
                        # Create file metrics change
                        metric = "kubernetes_configuration_change{{node=\"{0}\",file=\"{1}\"}} 1".format(host,
                                                                                                         config_file)
                        host_str["result"].append({'filename': config_file, 'value': diff_json});
                        # result[type]["list_servers"][host][config_file] = []
                        # result[type]["list_servers"][host][config_file] = diff_json

                    file.write(metric + "\n")

                result[type]["list_servers"].append(host_str)

    return result


if __name__ == '__main__':
    path_configs = '/home/vttek/Downloads/saocd/check_config/configs/'
    path_default_configs = '/home/vttek/Downloads/saocd/check_config/default-configs/'
    metric_path = '/home/vttek/Downloads/saocd/check_config/metrics'
    yaml_ignore_list = ['host', 'kubeadm.kubernetes.io/etcd.advertise-client-urls',
                        'kubeadm.kubernetes.io/kube-apiserver.advertise-address.endpoint']
    change_list = {}

    try:
        change_list = check_configs(path_configs, path_default_configs, metric_path, yaml_ignore_list)

        change_list["WORKER"] = {}
        change_list["WORKER"]["list_files"] = []
        change_list["WORKER"]["list_files"] = change_list["DB"]["list_files"]
        change_list["WORKER"]["list_servers"] = change_list["DB"]["list_servers"] + change_list["COMP"]["list_servers"]
        del change_list["DB"]
        del change_list["COMP"]

        json_change_list = json.dumps(change_list)
    except IOError as e:
        print(e)
    json_change_list = json.dumps(change_list)
    print(json_change_list)
    # for i in change_list:
    #    print(i)
    #    for u in change_list[i]:
    #        print(u)
    #        print(change_list[i][u])
    #        print('\033[1;34m' + '------------------------' + '\033[0m')
    #    print(
    #        '\033[1;31m' + '-------------------------------------------------------------------------------------'
    # + '\033[0m')
