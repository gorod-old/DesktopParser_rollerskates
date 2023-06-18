import json
import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from MessagePack import print_info_msg

DOT_ENV_KEY = 'dedta'


def generate_key(dot_env_key):
    folder = os.path.join(os.getcwd(), '.encrypted')
    if not os.path.exists(folder):
        os.mkdir(folder)
    key = Fernet.generate_key()
    file = os.environ.get(dot_env_key)
    file = dot_env_key if file is None else file
    key_path = os.path.join(folder, f'{file}.key')
    file = open(key_path, 'wb')
    file.write(key)
    file.close()
    return key


def get_key(dot_env_key):
    key = os.environ.get(dot_env_key)
    key = dot_env_key if not key else key
    key_path = os.path.join(os.getcwd(), '.encrypted', f'{key}.key')
    key_ = None
    if os.path.exists(key_path):
        file = open(key_path, 'rb')
        key_ = file.read()
        file.close()
    print_info_msg(f'key data: {key_}')
    return key_


def get_encrypted_path(dot_env_key):
    path = os.path.join(os.getcwd(), '.encrypted', f'{os.environ.get(dot_env_key)}.encrypted')
    print_info_msg(f'path: {path}')
    return path


def encrypt_data(dot_env_key, file_path):
    """Шифрует данные из файла (file_path) и сохраняет в папку .encrypted"""
    print_info_msg(f'file: {file_path}')
    key = generate_key(dot_env_key)
    fernet = Fernet(key)
    with open(file_path, 'rb') as file:
        data = file.read()
    encrypted = fernet.encrypt(data)
    print_info_msg(f'data: {encrypted}')
    # this writes your new, encrypted data into a new JSON file
    encrypted_file_path = get_encrypted_path(dot_env_key)
    with open(encrypted_file_path, 'wb') as file:
        file.write(encrypted)


def load_dotenv_data():
    key = get_key(DOT_ENV_KEY)
    if key is None:
        print_info_msg(f'start keys generate!')
        load_dotenv()
        encrypt_data('DOT_ENV_KEY', '.env')
        encrypt_data('GOOGLE_CREDENTIALS_KEY', os.environ.get('GOOGLE_CREDENTIALS_FILE'))
        return
    fernet = Fernet(key)
    encrypted_path = os.path.join(os.getcwd(), '.encrypted', f'{DOT_ENV_KEY}.encrypted')
    with open(encrypted_path, 'rb') as file:
        encrypted = file.read()
    data = fernet.decrypt(encrypted)
    dotenv_path = os.path.join(os.getcwd(), '.encrypted', DOT_ENV_KEY + '.env')
    with open(dotenv_path, 'wb') as file:
        file.write((''.join(chr(i) for i in data)).encode('charmap'))
    load_dotenv(dotenv_path)
    os.remove(dotenv_path)


def get_f_file(dot_env_key, ext):
    fernet = Fernet(get_key(dot_env_key))
    encrypted_path = get_encrypted_path(dot_env_key)
    with open(encrypted_path, 'rb') as file:
        encrypted = file.read()
    data = fernet.decrypt(encrypted)
    file_path = os.path.join(os.getcwd(), '.encrypted', f'{os.environ.get(dot_env_key)}.{ext}')
    print_info_msg(f'file: {file_path}')
    with open(file_path, 'w') as file:
        if ext == 'json':
            json_data = json.loads(data)
            json.dump(json_data, file)
    if ext == 'txt' or ext == 'env':
        with open(file_path, 'wb') as file:
            file.write((''.join(chr(i) for i in data)).encode('charmap'))
    return file_path


def del_f_file(dot_env_key, ext):
    file_path = os.path.join(os.getcwd(), '.encrypted', f'{os.environ.get(dot_env_key)}.{ext}')
    if os.path.exists(file_path):
        os.remove(file_path)

