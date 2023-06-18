import os

from colorama import Fore, Style


class Parser:
    _proxy_api = None
    _proxy_auth = False
    __number = 0
    _user_agents_list = []
    _proxies_list = []
    _api_proxies_list = []
    __img_names = []

    def __new__(cls, *args, **kwargs):
        cls.__number += 1
        print(Fore.YELLOW + f'[INFO]  start {cls.__name__}', Fore.CYAN + f'{cls.__number}')
        cls._set_variables()
        return super(Parser, cls).__new__(cls)

    def __init__(self):
        super(Parser, self).__init__()
        self._current_proxy = None
        self._get_proxies()
        self._encoding = 'utf-8'
        self._max_retry = 5
        self._except_print = False
        self._stream = 1

    def get_page_text(self, url: str, proxy: bool, time_limit: float, request_timeout,
                      random_wait, driver_setup=None):
        """Gets the text of a web page.\n
        time_limit - total time to get the result.\n
        request_timeout - max time delay for one request"""
        print(Fore.YELLOW + '[INFO  get_page_text]', Style.RESET_ALL + 'this method of base class Parser does nothing')

    @classmethod
    def _set_variables(cls):
        if os.path.exists(os.getcwd() + '/text_files/user-agents.txt'):
            cls._user_agents_list = cls.__get_user_agents_list()
        else:
            print(Fore.YELLOW + '[INFO]', Style.RESET_ALL +
                  f' user-agents.txt - not found, by default the user_agent module will be used for generation.')
        if os.path.exists(os.getcwd() + '/text_files/proxies.txt'):
            cls._proxies_list = cls.__get_proxies_list()
        elif len(cls._proxies_list) == 0:
            print(Fore.YELLOW + '[INFO]', Style.RESET_ALL +
                  f' proxies.txt - not found, using a proxy is not possible.')
        print(Fore.YELLOW + f'[INFO]  proxy api: ', Fore.MAGENTA + f'{cls._proxy_api}')
        cls._api_proxies_list = cls.__get_api_proxy_list()

    @classmethod
    def __get_user_agents_list(cls):
        ua_list = open('text_files/user-agents.txt').read().strip().split('\n')
        for ua in ua_list:
            if len(ua) == 0:
                ua_list.remove(ua)
        print(Fore.YELLOW + '[INFO]', Style.RESET_ALL + f' user agent list count: ' + Fore.CYAN + f'{len(ua_list)}')
        return ua_list

    @classmethod
    def __get_proxies_list(cls):
        p_list = open('text_files/proxies.txt').read().strip().split('\n')
        for p in p_list:
            if len(p) == 0:
                p_list.remove(p)
        print(Fore.YELLOW + '[INFO]', Style.RESET_ALL + f' proxies list count: ' + Fore.CYAN + f'{len(p_list)}')
        return p_list

    @classmethod
    def __get_api_proxy_list(cls):
        if cls._proxy_api is None:
            return None
        print(Fore.YELLOW + '[INFO]  Getting a list of active proxies from api')
        p_list = []
        for func in cls._proxy_api:
            p_list += func(cls._proxy_auth)
        print(Fore.YELLOW + '[INFO]  Received proxies from api:', Fore.CYAN + f' {len(p_list)}')
        print(p_list)
        return p_list

    def _get_proxies(self):
        self._proxies = [proxy for proxy in self._api_proxies_list] if self._api_proxies_list \
            else [proxy for proxy in self._proxies_list]

    @classmethod
    def set_marker(cls, marker: str):
        if marker:
            print(Fore.YELLOW + f'[INFO]  {cls.__name__}', Fore.MAGENTA + f' {marker}')

    @property
    def current_proxy(self):
        return self._current_proxy

    @property
    def max_retry(self):
        return self._max_retry

    @property
    def encoding(self):
        return self._encoding

    @property
    def except_print(self):
        return self._except_print

    def save_images(self, src_list, root_folder: str, project_folder: str = None, folder: str = 'images',
                    max_size: int = None):
        for src in src_list:
            self.save_img(src, root_folder, project_folder, folder, max_size)

    def save_img(self, src: str, root_folder: str = 'result data', project_folder: str = None, folder: str = 'images',
                 max_size: int = None):
        """Saves the image and returns the file path."""
        if root_folder is None or root_folder == '':
            print(Fore.YELLOW + 'INFO', Style.RESET_ALL + ' no root folder specified for output data, set to: '
                  + Fore.CYAN + 'result data')
            root_folder = 'result data'
        root = os.getcwd() + f'/{root_folder}'
        if not os.path.exists(root) or not os.path.isdir(root):
            os.mkdir(root)
        project_folder = '/' + project_folder if project_folder is not None else ''
        if project_folder != '' and (
                not os.path.exists(root + project_folder) or not os.path.isdir(root + project_folder)):
            os.mkdir(root + project_folder)
        folder = '/' + folder if folder is not None else ''
        if folder != '' and (not os.path.exists(root + project_folder + folder) or
                             not os.path.isdir(root + project_folder + folder)):
            os.mkdir(root + project_folder + folder)
        path = root + project_folder + folder
        name = self.__get_image_name(src)
        extension = self.__get_image_extension(src)
        path += '/' + name + extension
        return os.path.normpath(path)

    @classmethod
    def __get_image_name(cls, url):
        name = ''
        parts = url.split('?')[0].split('/')[-1].split('.')
        for i, p in enumerate(parts):
            name += p if i < len(parts) - 1 else ''
            name += '_' if i < len(parts) - 2 else ''
        i = 1
        name_ = name
        for n in cls.__img_names:
            if name_ == n:
                name_ = name + f'_{i}'
                i += 1
        cls.__img_names.append(name_)
        return name_

    @classmethod
    def __get_image_extension(cls, url):
        parts = url.split('?')[0].split('.')
        ext = '.' + parts[len(parts) - 1]
        return ext
