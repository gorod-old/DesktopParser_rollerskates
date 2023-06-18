import os
from random import uniform, choice
from time import sleep

import numpy as np
from PyQt5.QtCore import QThread
from colorama import Fore, Style
from selenium import webdriver
from selenium.webdriver.common.by import By

from MessagePack import print_exception_msg, print_info_msg
from WebDriverPack import WebDriver
from WebDriverPack.webDriver import try_func, timer_func
from g_gspread import update_sheet_data as gspread_update, get_sheet_data_by_id, add_sheet_data

DEV = False
HEADLESS = True
HEADER = ['URL', 'Короткое название', 'Размер', 'Изменение', 'Стелька']
header_data = []
data = []


class SiteParser(QThread):
    def __init__(self, app, name, stream):
        super().__init__()
        self.app = app
        self.name = name
        self.stream = stream
        self.spreadsheet_id = os.environ.get('SPREADSHEET_ID') if DEV else os.environ.get('SPREADSHEET_ID_PROD')
        self.sheet_id = int(os.environ.get('SHEET_ID')) if DEV else int(os.environ.get('SHEET_ID_PROD'))

    def add_row_info(self, row, index_1=None, index_2=None):
        check = np.array(row)
        empty = True
        for cell in row:
            if cell != '':
                empty = False
                break
        if len(row) == 0 or empty:
            return
        for r in data:
            if np.array_equal(check, np.array(r)):
                return
        index_1 = '' if index_1 is None else Fore.BLUE + f'[{index_1}]'
        index_2 = '' if index_2 is None else Fore.BLUE + f'[{index_2}]'
        print(Fore.YELLOW + f'[PARSER {self.stream}]', index_1, index_2, Style.RESET_ALL + f'{row}')
        data.append(row)

    def info_msg(self, msg):
        print(Fore.YELLOW + f'[PARSER {self.stream}]', msg, Style.RESET_ALL)

    def delete(self):
        if self.driver:
            print('del driver for', self.name)
            self.driver.close()

    def _create_driver(self):
        self.driver = WebDriver(headless=HEADLESS)

    def run(self):
        self.info_msg(f'start parser: {self.name}')
        self._create_driver()
        data_ = pars_data(self)
        if data_ and len(data_) > 0:
            gspread_update(header_data, None, self.spreadsheet_id, self.sheet_id)
            add_sheet_data('A5', data_, self.spreadsheet_id, self.sheet_id)
        self.app.end_pars()
        self.driver.close()
        self.quit()


@timer_func
@try_func
def pars_data(parser):
    data.clear()
    header_data.clear()
    app = parser.app
    driver = parser.driver
    driver.driver.maximize_window()
    # get spreadsheet data
    ss_id = parser.spreadsheet_id
    sheet_id = parser.sheet_id
    print(ss_id, sheet_id)
    ss_data = get_sheet_data_by_id(ss_id, sheet_id)
    print('ss data count:', len(ss_data))
    # print(ss_data)
    # for row in ss_data:
    #     print(row)
    for i, row in enumerate(ss_data):
        if not app.run:
            return None
        if i <= 3:
            header_data.append(row)
        elif i > 3 and len(row) > 0 and row[0] != '':
            url = row[0]
            name = row[1]
            url_rus = row[5]
            len_ = ''
            # get sizes data
            check = None
            for k in range(3):
                try:
                    driver.get_page(url)
                    driver.waiting_for_element((By.CSS_SELECTOR, '#productTabs > li:nth-child(3) > a'), 10)
                    tab = driver.get_element((By.CSS_SELECTOR, '#productTabs > li:nth-child(3) > a'))
                    driver.driver.execute_script("arguments[0].scrollIntoView();", tab)
                    webdriver.ActionChains(driver.driver).move_to_element(tab).click().perform()
                    sleep(1)
                    in_stock = driver.get_elements(
                        (By.CSS_SELECTOR, '#pricelist > tbody > tr.hidden-xs > td:nth-child(1) > span > span'))
                    sizes = driver.get_elements(
                        (By.CSS_SELECTOR, '#pricelist > tbody > tr.hidden-xs > td:nth-child(2) > b'))
                    print('in stock count:', len(in_stock), 'sizes count:', len(sizes))
                    if in_stock and sizes:
                        check = []
                        for j, el in enumerate(in_stock):
                            if el.get_attribute('class') == 'label label-success':
                                size = sizes[j].text
                                if "Manufacturer's label:" in size:
                                    size = size.split("Manufacturer's label:")[1].split('/')[0].strip()
                                else:
                                    size = size.split('/')[0].strip()
                                size = size.split('.')[0].replace('S', 'US ')
                                check.append(size)
                    parser.info_msg(f'check: {check}')
                    if check is not None:
                        break
                except Exception as e:
                    print_exception_msg(str(e))
            if check is None or len(check) == 0:
                row_ = [url, name, '', '', len_]
                data.append(row_)
                parser.info_msg(str(row_))
            else:
                num, j = 0, i
                while j < len(ss_data) and ss_data[j][2] != '' and (num == 0 or ss_data[j][0] == ''):
                    row_ = [url] if num == 0 else ['']
                    row_.append(name)
                    if ss_data[j][3] == '+' or ss_data[j][3] == '':
                        if ss_data[j][2] not in check:
                            row_.append(ss_data[j][2])
                            row_.append('-')
                        else:
                            row_.append(ss_data[j][2])
                            row_.append('')
                            check.remove(ss_data[j][2])
                        row_.append(len_)
                        row_.append(url_rus)
                        data.append(row_)
                        parser.info_msg(str(row_))
                        num += 1
                    j += 1
                for size in check:
                    row_ = [url, name, size, '+', len_, url_rus] if num == 0 else ['', name, size, '+', len_, url_rus]
                    data.append(row_)
                    parser.info_msg(str(row_))
                    num += 1
            parser.app.set_counter(url)
    return data
