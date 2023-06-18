import math
import threading
from time import perf_counter, sleep
from typing import Any

from colorama import Fore, Style


def __time_str(num):
    if num < 10:
        return '0' + str(num)
    return str(num)


def get_time(sec):
    """Return time string in format 00:00:00"""
    hour_ = math.trunc(sec / 3600)
    min_ = math.trunc(sec % 3600 / 60)
    sec_ = math.trunc(sec % 3600 % 60)
    return __time_str(hour_) + ':' + __time_str(min_) + ':' + __time_str(sec_)


class AsyncProcess:
    def __init__(self, name, function, stream_num, callback: tuple[object, Any] = None, timeout: float = 1, args=()):
        super(AsyncProcess, self).__init__()
        self.name = name
        self.start_time = perf_counter()
        print(Fore.BLUE + '[ASYNC PROCESS]', Style.RESET_ALL +
              f' process: "{self.name}", start time: ', self.start_time)
        self.stream_list = []
        self.stream_num = stream_num
        self.callback = callback
        for num in range(stream_num):
            args_ = args
            if stream_num > 1:
                args_ = args + (num + 1,)  # добавляем номер процесса
            self.stream_list.append(threading.Thread(target=function, args=args_))
            self.stream_list[num].start()
            sleep(timeout)
        t = threading.Thread(target=self.waiting_for_process_end, args=())
        t.start()

    def waiting_for_process_end(self):
        for num in range(self.stream_num):
            self.stream_list[num].join()
        ov_time = perf_counter() - self.start_time
        print(Fore.BLUE + '[ASYNC PROCESS]', Style.RESET_ALL +
              f' process: "{self.name}", end time: ', perf_counter())
        print(Fore.BLUE + '[ASYNC PROCESS]', Style.RESET_ALL +
              f' process: "{self.name}" - completed, total time: ', get_time(ov_time), ' sec')
        print('________________________________________________________')
        if self.callback:
            self.call_method(*self.callback)

    @classmethod
    def call_method(cls, instance, method):
        if instance is None or type(method) is not str:
            try:
                method()
            except Exception as e:
                if type(method) is str:
                    print(Fore.MAGENTA + '[ERROR]',
                          Fore.CYAN + f' function named {method} not find, specify a method reference instead' +
                          ' of a name, or add a reference to an instance of the class as the first argument.')
                else:
                    print(Fore.MAGENTA + '[ERROR]',
                          Fore.CYAN + f' function named {method} not find in globals scope',
                          Style.RESET_ALL + f'{str(e)}')
            return
        try:
            class_method = getattr(type(instance), method)
            class_method(instance)
        except Exception as e:
            print(Fore.MAGENTA + '[ERROR]',
                  Fore.CYAN + f' function named {method} not find. ',
                  Style.RESET_ALL + f'{str(e)}')