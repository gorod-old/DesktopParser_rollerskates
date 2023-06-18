import json
import os

from MessagePack import print_info_msg


def save_json(json_data, root_folder: str = '', file_name: str = 'result', encoding='utf-8', folder: str = None):
    path = __get_file_path('json', root_folder=root_folder, file_name=file_name, folder=folder)
    print_info_msg(msg=f'save path: {path}')
    if os.path.exists(path):
        os.remove(path)
    with open(path, 'a', encoding=encoding) as file:
        json.dump(json_data, file, indent=4, ensure_ascii=False)


def get_json_data_from_file(path, encoding='utf-8', stream: int = None):
    print_info_msg(msg=f'get data path: {path}', stream=stream)
    json_content = open(path, 'r', encoding=encoding).read()
    json_data = json.loads(json_content)
    return json_data


def __get_file_path(extension: str, root_folder: str = 'result data', file_name: str = 'result', folder: str = None):
    if root_folder is None or root_folder == '':
        print_info_msg(msg=f'no root folder specified for output data, set to: None')
        root_folder = None
    root = os.getcwd() + f'/{root_folder}' if root_folder is not None else os.getcwd()
    if not os.path.exists(root) or not os.path.isdir(root):
        os.mkdir(root)
    folder = '/' + folder if folder is not None else ''
    if folder != '' and (not os.path.exists(root + folder) or not os.path.isdir(root + folder)):
        os.mkdir(root + folder)
    path = root + folder + f'/{file_name}.{extension}'
    return os.path.normpath(path)
