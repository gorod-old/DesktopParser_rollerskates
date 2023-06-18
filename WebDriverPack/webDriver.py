import os
import shutil
import sys
from subprocess import CREATE_NO_WINDOW

import urllib3
import zipfile
from time import sleep, time

from selenium.webdriver.chrome.service import Service
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver import DesiredCapabilities

from MessagePack import print_exception_msg, print_info_msg
from MessagePack.message import err_log
from ServiceApiPack import solve_recaptcha_guru, solve_img_captcha_guru

import pydub
import speech_recognition as sr

from colorama import Fore, Style
from random import choice, uniform

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from ParserPack import Parser
from WebDriverPack.patch import webdriver_folder_name, download_latest_chromedriver
from WinSoundPack import beep
# from saveData import resize_image


def timer_func(func):
    """This function shows the execution time of
    the function object passed"""
    def wrap_func(*args, **kwargs):
        t1 = time()
        result = func(*args, **kwargs)
        t2 = time()
        delta = t2-t1
        print(f'Function {func.__name__!r} executed in:\n {delta :.4f}s, {convert_sec_to_time_string(delta)}')
        return result
    return wrap_func


def try_func(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # print_exception_msg(msg=str(e))
            pass
    return wrapper


def convert_sec_to_time_string(seconds):
    """ Convert time value in seconds to time data string - 00:00:00"""
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return "%02d:%02d:%02d" % (hour, minutes, seconds)


class DriverSetup:
    def __init__(self, headless: bool = False, delay_time: float = 3,
                 el_max_wait_time: float = 3, element=None,
                 el_has_css_class=None,
                 form_data=None,
                 captcha: str = None,
                 captcha_image_element=None,
                 captcha_image_input=None,
                 submit_button=None,
                 submit_check_element=None):
        super(DriverSetup, self).__init__()
        self.headless = headless
        self.delay_time = delay_time
        self.element = element
        self.el_max_wait_time = el_max_wait_time
        self.el_has_css_class = el_has_css_class
        self.form_data = form_data
        self.captcha = captcha
        self.captcha_image_element = captcha_image_element
        self.captcha_image_input = captcha_image_input
        self.submit_button = submit_button
        self.submit_check_element = submit_check_element


class ElementHasCssClass(object):
    """An expectation for checking that an element has a particular css class.

    locator - used to find the element
    returns the WebElement once it has the particular css class
    """

    def __init__(self, locator, css_class: str):
        self.locator = locator
        self.css_class = css_class

    def __call__(self, driver):
        element = driver.find_element(*self.locator)  # Finding the referenced element
        if self.css_class in element.get_attribute("class"):
            return element
        else:
            return False


class WebDriver(Parser):
    __number = 0

    def __new__(cls, *args, **kwargs):
        cls.__number += 1
        cls._proxy_api = kwargs.get('proxy_api')
        cls._proxy_auth = kwargs.get('proxy_auth')
        return super(WebDriver, cls).__new__(cls)

    def __init__(self, marker: str = None, user_agent: bool = True, proxy=False, proxy_api: list = None,
                 proxy_auth: bool = False, except_print: bool = False, delay_time: float = 3,
                 headless: bool = False, max_retry: int = 5, stream: int = None,
                 window_width: int = 1920, window_height: int = 1080, rem_warning=False, full_screen=False,
                 wait_full_page_download=True):
        super(WebDriver, self).__init__()
        print(Fore.YELLOW + '[INFO]  marker:', Fore.MAGENTA + f'{marker}')
        self._proxy = proxy
        self._proxy_api = proxy_api
        self._proxy_auth = proxy_auth
        self._except_print = except_print
        self._user_agent = user_agent
        self._delay_time = delay_time
        self._headless = headless
        self._max_retry = max_retry
        self._stream = stream
        self._driver = self._get_driver(window_width, window_height, rem_warning, full_screen, wait_full_page_download)

    def __del__(self):
        try:
            self._driver.quit()
        except Exception as e:
            self.print_msg(location='WebDriver __del__', msg=f'{str(e)}', exception=True, stream=self.stream)

    def close(self):
        try:
            self._driver.quit()
        except Exception as e:
            self.print_msg(location='WebDriver __del__', msg=f'{str(e)}', exception=True, stream=self.stream)

    @property
    def current_url(self):
        return self._driver.current_url

    @property
    def stream(self):
        return self._stream

    @property
    def driver(self):
        return self._driver

    @classmethod
    def _get_user_agent(cls):
        return choice(cls._user_agents_list) if len(cls._user_agents_list) > 0 else None

    def _get_proxy(self, proxy):
        if type(proxy) is bool:
            if len(self._proxies) == 0:
                return None
            proxy = self._current_proxy
            while proxy == self._current_proxy:
                if len(self._proxies) == 1 and proxy in self._proxies:
                    break
                proxy = choice(self._proxies)
            self._proxies.remove(proxy)
            self._current_proxy = proxy
            if len(self._proxies) == 0:
                self._get_proxies()
        return proxy

    def _get_driver(self, width, height, rem_warning, full_screen, wait_full_page_download=True):
        if not os.path.exists('C:/Program Files/Google/Chrome/Application/chrome.exe'):
            sys.exit(
                "[ERR] Please make sure Chrome browser is installed "
                "(path is exists: C:/Program Files/Google/Chrome/Application/chrome.exe) "
                "and updated and rerun program"
            )
        # download latest chromedriver, please ensure that your chrome is up to date
        driver = None
        while True:
            try:
                # create chrome driver
                path_to_chromedriver = os.path.normpath(
                    os.path.join(os.getcwd(), webdriver_folder_name, "chromedriver.exe")
                )
                service = Service(path_to_chromedriver)
                service.creationflags = CREATE_NO_WINDOW
                options = webdriver.ChromeOptions()
                options.headless = self._headless
                options.add_argument("--window-size=%s" % f"{width},{height}")
                if rem_warning:
                    options.add_argument("--disable-infobars")  # removes a warning
                if full_screen:
                    options.add_argument("--kiosk")  # open in full screen
                if self._user_agent:
                    u_agent = self._get_user_agent()
                    print(Fore.YELLOW + '[INFO]', Style.RESET_ALL + f" user-agent: {u_agent}")
                    if u_agent:
                        options.add_argument('user-agent=' + u_agent)
                if self._proxy:
                    prx = self._get_proxy(self._proxy)
                    self.print_msg(msg=f'driver proxy: {prx}', stream=self.stream)
                    if prx is not None:
                        auth_plugin = self._proxy_auth_plugin(prx)
                        if auth_plugin:
                            options.add_extension(auth_plugin)
                        else:
                            options.add_argument('--proxy-server=' + prx)
                save_path = os.path.normpath(os.getcwd() + f'/Downloads')
                if not os.path.exists(save_path):
                    os.mkdir(save_path)
                save_path = os.path.normpath(os.getcwd() + f'/Downloads/{self.stream}')
                if not os.path.exists(save_path):
                    os.mkdir(save_path)
                options.add_experimental_option("prefs", {
                    "download.default_directory": f"{save_path}",
                    "download.prompt_for_download": False,
                    "download.directory_upgrade": True,
                    "safebrowsing.enabled": True
                })
                caps = DesiredCapabilities().CHROME
                if wait_full_page_download:
                    caps["pageLoadStrategy"] = "normal"  # Waits for full page load
                else:
                    caps["pageLoadStrategy"] = "none"  # Do not wait for full page load
                driver = webdriver.Chrome(desired_capabilities=caps, service=service, options=options)
                self.__delay(driver, self._delay_time)
                return driver
            except Exception as e:
                self.print_msg(location='WebDriver _get_driver()', msg=f'{str(e)}', exception=True, stream=self.stream)
                # patch chromedriver if not available or outdated
                if driver is None:
                    is_patched = download_latest_chromedriver()
                else:
                    is_patched = download_latest_chromedriver(
                        driver.capabilities["version"]
                    )
                if not is_patched:
                    err_log("webDriver[get_driver]",
                            "[ERR] Please update the chromedriver.exe in the webdriver folder "
                            "according to your chrome version: https://chromedriver.chromium.org/downloads")
                    sys.exit(
                        "[ERR] Please update the chromedriver.exe in the webdriver folder "
                        "according to your chrome version: https://chromedriver.chromium.org/downloads"
                    )

    def _proxy_auth_plugin(self, proxy):
        if proxy is None:
            return None
        proxy = proxy.replace('@', ':').split(':')
        if len(proxy) == 2:
            return None
        proxy_host = proxy[2]
        proxy_port = proxy[3]
        proxy_user = proxy[0]
        proxy_pass = proxy[1]

        manifest_json = """
        {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Chrome Proxy",
            "permissions": [
                "proxy",
                "tabs",
                "unlimitedStorage",
                "storage",
                "<all_urls>",
                "webRequest",
                "webRequestBlocking"
            ],
            "background": {
                "scripts": ["background.js"]
            },
            "minimum_chrome_version":"22.0.0"
        }
        """

        background_js = """
        var config = {
                mode: "fixed_servers",
                rules: {
                singleProxy: {
                    scheme: "http",
                    host: "%s",
                    port: parseInt(%s)
                },
                bypassList: ["localhost"]
                }
            };

        chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

        function callbackFn(details) {
            return {
                authCredentials: {
                    username: "%s",
                    password: "%s"
                }
            };
        }

        chrome.webRequest.onAuthRequired.addListener(
                    callbackFn,
                    {urls: ["<all_urls>"]},
                    ['blocking']
        );
        """ % (proxy_host, proxy_port, proxy_user, proxy_pass)

        plugin = f'proxy_auth_plugin_{self._stream}.zip'
        with zipfile.ZipFile(plugin, 'w') as zp:
            zp.writestr("manifest.json", manifest_json)
            zp.writestr("background.js", background_js)
        return plugin

    def _reset_driver(self):
        self._driver.quit()
        self._driver = self._get_driver()

    def change_proxy(self, setup: DriverSetup = None, random_wait: tuple = (.5, 3)):
        if not self._proxy or len(self._proxies) == 0:
            self.print_msg(location='WebDriver _reset_driver',
                           msg=f'Proxies list is empty or proxy is not set',
                           stream=self.stream)
            return
        url = self.current_url
        self._driver = self._get_driver()
        self.get_page(url, setup.el_max_wait_time, setup.element, setup.el_has_css_class, setup.form_data,
                      setup.captcha, setup.captcha_image_element, setup.captcha_image_input,
                      setup.submit_button, setup.submit_check_element, random_wait)

    @classmethod
    def __delay(cls, driver, delay_time):
        driver.implicitly_wait(delay_time)

    def get_page_text(self, url, proxy, time_limit, request_timeout, random_wait,
                      setup: DriverSetup = None):
        if self.get_page(url, setup.el_max_wait_time, setup.element, setup.el_has_css_class, setup.form_data,
                         setup.captcha, setup.captcha_image_element, setup.captcha_image_input,
                         setup.submit_button, setup.submit_check_element, random_wait):
            return self._driver.page_source
        return None

    def get_page(self, url: str, el_max_wait_time: float = 3,
                 element=None,
                 el_has_css_class=None,
                 form_data=None,
                 captcha: str = None,
                 captcha_image_element=None,
                 captcha_image_input=None,
                 submit_button=None,
                 submit_check_element=None,
                 random_wait: tuple = (.5, 3)):
        """Get web page by url.
        element: tuple[By, str];
        el_has_css_class: tuple[element[By, str], class];
        form_data: list[input data[element[By, 'str'], text], ...];
        recaptcha_image_element: tuple[By, str];
        submit_button: tuple[By, str];
        submit_check_element: list[element[By, str], partial_text];
        """

        for i in range(self._max_retry):
            try:
                sleep(uniform(*random_wait))
                self._driver.get(url)
                # self.print_msg(location='WebDriver get_page',
                #                msg=f'driver current url: {self._driver.current_url}',
                #                stream=self.stream)

                # page element waiting
                wait = WebDriverWait(self._driver, el_max_wait_time)
                if element:
                    element = wait.until(EC.presence_of_element_located(element))
                elif el_has_css_class:
                    element = wait.until(ElementHasCssClass(el_has_css_class[0], el_has_css_class[1]))

                # form input
                if form_data:
                    self._form_input(form_data)
                    if not captcha:
                        self._submit_bt_click(submit_button)
                        # form submit check
                        if not submit_check_element:
                            self.print_msg(location='WebDriver get_page',
                                           msg=f'Form or recaptcha submission is determined by a change in the url, '
                                               f'\nset the validation element if the url does not change as a result '
                                               f'of the submission, \nor for better identification!',
                                           stream=self.stream)
                        if (submit_check_element and self._check_element(submit_check_element, el_max_wait_time)) \
                                or self._driver.current_url != url:
                            self.print_msg(location='WebDriver get_page',
                                           msg=f'Form submit check: passed. Form data is submitted',
                                           stream=self.stream)
                        else:
                            self.print_msg(location='WebDriver get_page',
                                           msg=f'Failed to confirm the data submission. Form submit check: not passed',
                                           stream=self.stream)
                # captcha
                solved = False
                if captcha and (self._check_element([(By.CSS_SELECTOR, 'div.g-recaptcha'), None])
                                or captcha == 'v2'):
                    solved = self.recaptcha_v2_solver(submit_button, submit_check_element)
                    if not solved:
                        solved = self.recaptcha_solver_api(submit_button, submit_check_element)
                elif captcha == 'v3':
                    pass
                elif captcha == 'image':
                    solved = self.captcha_image_solver_api(captcha_image=captcha_image_element,
                                                           response=captcha_image_input, submit=submit_button,
                                                           submit_check_element=submit_check_element)
                return not captcha or solved
            except Exception as e:
                print_exception_msg(str(e))
                # self.print_msg(location='WebDriver get_page', msg=f'{str(e)}', stream=self.stream)
                self._reset_driver()
        return False

    def _check_url(self, url):
        return self._driver.current_url == url

    def _form_input(self, data):
        """fills in all form fields"""
        print(Fore.YELLOW + '[INFO]  _form_input')
        if data is None:
            return
        for inp_data in data:
            sleep(uniform(.5, 3.0))
            print(Fore.YELLOW + '[INFO]', Style.RESET_ALL + f' form input: {inp_data[0][1]}' + Fore.CYAN + ' true')
            element = self._driver.find_element(*inp_data[0])
            offset = self.get_element_offset(element)
            action = webdriver.ActionChains(self._driver)
            action.move_to_element_with_offset(element, offset['x'], offset['y']).pause(uniform(1.0, 2.0)) \
                .send_keys_to_element(element, *inp_data[1]).perform()

    def _check_element(self, element_data, el_max_wait_time: float = 3):
        """check if an element exists on the page"""
        element = element_data[0]
        text = element_data[1]
        try:
            wait = WebDriverWait(self._driver, el_max_wait_time)
            wait.until(EC.presence_of_element_located(element))
            if text and text not in self._driver.find_element(*element).text:
                return False
        except Exception as e:
            if self.except_print:
                print(Fore.MAGENTA + '[ERROR]', Style.RESET_ALL +
                      f"in _check_element() - Element not find. \n - {str(e)}")
            return False
        return True

    @try_func
    def get_element(self, element):
        if self._driver.current_url == 'data:,':
            return None
        return self._driver.find_element(*element)

    @try_func
    def get_elements(self, element):
        if self._driver.current_url == 'data:,':
            return None
        return self._driver.find_elements(*element)

    @try_func
    def get_element_in_element(self, in_el: WebElement, element):
        if self._driver.current_url == 'data:,':
            return None
        return in_el.find_element(*element)

    @try_func
    def get_elements_in_element(self, in_el: WebElement, element):
        if self._driver.current_url == 'data:,':
            return None
        return in_el.find_elements(*element)

    @try_func
    def get_el_attribute(self, element,
                         in_element, *attrs):
        data = []
        if not (type(element) is tuple or type(element) is WebElement):
            return []
        if in_element:
            els = self.get_elements_in_element(in_element, element) if type(element) is not WebElement else [element]
        else:
            els = self.get_elements(element) if type(element) is not WebElement else [element]
        for el in els:
            attrs_ = []
            for attr in attrs:
                if attr == 'text':
                    attrs_.append(el.text)
                else:
                    attrs_.append(el.get_attribute(attr))
            data.append(attrs_)
        return data

    def send_keys(self, element: WebElement, key: str):
        action = webdriver.ActionChains(self._driver)
        action.send_keys_to_element(element, key).pause(uniform(.1, .5))\
            .send_keys_to_element(element, Keys.ENTER).perform()

    def waiting_for_element(self, element: tuple, wait_time: int):
        try:
            WebDriverWait(self._driver, wait_time).until(EC.presence_of_element_located(
                element))
        except Exception as e:
            self.print_msg('WebDriver waiting_for_element', 'element timeout exceeded', True, self.stream)

    @classmethod
    def get_element_offset(cls, element):
        """Set offset of the specified element.
        Offsets are relative to the top-left corner of the element.

        returned {'x': x_offset, 'y': y_offset}"""

        x_offset = uniform(element.size['width'] * .1, element.size['width'] * .4)
        y_offset = uniform(element.size['height'] * .1, element.size['height'] * .9)
        return {'x': x_offset, 'y': y_offset}

    def _submit_bt_click(self, submit):
        try:
            self._driver.switch_to.default_content()
            sleep(uniform(1.0, 5.0))
            element = self._driver.find_element(*submit)
            offset = self.get_element_offset(element)
            action = webdriver.ActionChains(self._driver)
            action.move_to_element_with_offset(element, offset['x'], offset['y']) \
                .pause(uniform(1.0, 2.0)).click().perform()
        except Exception as e:
            if self.except_print:
                print(Fore.MAGENTA + '[EXCEPT]', Style.RESET_ALL +
                      f' in WebDriver._submit_bt_click(self, submit): recaptcha submit not find, '
                      f'\n{str(e)}')

    def recaptcha_v2_solver(self, submit=None,
                            submit_check_element=None):
        print(Fore.YELLOW + '[INFO]  recaptcha_v2_solver')
        start_url = self._driver.current_url
        recaptcha_control_frame = None
        recaptcha_challenge_frame = None
        for i in range(2):
            # find recaptcha frames
            sleep(uniform(1.0, 5.0))
            frames = self._driver.find_elements(By.TAG_NAME, "iframe")
            print(Fore.YELLOW + '[INFO]', Style.RESET_ALL + f' iframes count: {len(frames)}')
            for index, frame in enumerate(frames):
                if frame.get_attribute("title") == "reCAPTCHA":
                    recaptcha_control_frame = frame
                if frame.get_attribute("title") == "проверка recaptcha":
                    recaptcha_challenge_frame = frame
            if not recaptcha_control_frame or not recaptcha_challenge_frame:
                print(Fore.MAGENTA + '[ERR]', Style.RESET_ALL + " Unable to find recaptcha.")
                if submit and i == 0:
                    self._submit_bt_click(submit)
                else:
                    # form submit check
                    if not submit_check_element:
                        print(Fore.YELLOW + '[INFO]', Fore.MAGENTA +
                              'Form or recaptcha submission is determined by a change in the url, set the validation '
                              'element if the url does not change as a result of the submission, \nor for better '
                              'identification!')
                    if (submit_check_element and self._check_element(submit_check_element)) \
                            or self._driver.current_url != start_url:
                        print(Fore.YELLOW + '[INFO]  Submit check:', Fore.CYAN + f" passed")
                        print(Fore.YELLOW + '[INFO]', Style.RESET_ALL + f" data is submitted")
                        return True
                    else:
                        print(Fore.YELLOW + '[INFO]', Style.RESET_ALL + f" failed to confirm the data submission")
                        print(Fore.YELLOW + '[INFO]  Submit check:', Fore.CYAN + f" not passed")
                    print(Fore.YELLOW + '[INFO]', Fore.CYAN + " Abort solver.")
                    raise ValueError('raise exception to reset driver.')
            else:
                break

        # switch to recaptcha frame
        self._driver.find_elements(By.TAG_NAME, "iframe")
        self._driver.switch_to.frame(recaptcha_control_frame)

        # click on checkbox to activate recaptcha
        sleep(uniform(1.0, 5.0))
        element = self._driver.find_element(By.CLASS_NAME, "recaptcha-checkbox-border")
        offset = self.get_element_offset(element)
        action = webdriver.ActionChains(self._driver)
        action.move_to_element_with_offset(element, offset['x'], offset['y']) \
            .pause(uniform(1.0, 2.0)).click().perform()
        print(Fore.YELLOW + '[INFO]', Style.RESET_ALL + f' recaptcha-checkbox is clicked')
        sleep(3)
        if 'display: none' in element.get_attribute('style'):
            print(Fore.YELLOW + '[INFO]  Recaptcha pass check: ' + Fore.CYAN + 'passed')
            if submit:
                self._submit_bt_click(submit)
                # form submit check
                if not submit_check_element:
                    print(Fore.YELLOW + '[INFO]', Fore.MAGENTA +
                          'Form or recaptcha submission is determined by a change in the url, set the validation '
                          'element if the url does not change as a result of the submission, \nor for better '
                          'identification!')
                if (submit_check_element and self._check_element(submit_check_element)) \
                        or self._driver.current_url != start_url:
                    print(Fore.YELLOW + '[INFO]  Submit check:', Fore.CYAN + f" passed")
                    print(Fore.YELLOW + '[INFO]', Style.RESET_ALL + f" data is submitted")
                else:
                    print(Fore.YELLOW + '[INFO]', Style.RESET_ALL + f" failed to confirm the data submission")
                    print(Fore.YELLOW + '[INFO]  Submit check:', Fore.CYAN + f" not passed")
            print(Fore.YELLOW + '[INFO]', Style.RESET_ALL + f" Recaptcha is passed")
            return True

        # switch to recaptcha audio control frame
        self._driver.switch_to.default_content()
        self._driver.find_elements(By.TAG_NAME, "iframe")
        self._driver.switch_to.frame(recaptcha_challenge_frame)

        # click on audio challenge
        sleep(uniform(1.0, 5.0))
        element = self._driver.find_element(By.ID, "recaptcha-audio-button")
        offset = self.get_element_offset(element)
        action = webdriver.ActionChains(self._driver)
        action.move_to_element_with_offset(element, offset['x'], offset['y']). \
            pause(uniform(1.0, 2.0)).click().perform()
        print(Fore.YELLOW + '[INFO]', Style.RESET_ALL + f' recaptcha-audio-button is clicked')

        # switch to recaptcha audio challenge frame
        self._driver.switch_to.default_content()
        self._driver.find_elements(By.TAG_NAME, "iframe")
        self._driver.switch_to.frame(recaptcha_challenge_frame)

        for i in range(5):
            # get the mp3 audio file
            sleep(uniform(1.0, 5.0))
            src = self._driver.find_element(By.ID, "audio-source").get_attribute("src")
            print(Fore.YELLOW + '[INFO]', Style.RESET_ALL + f" Audio src: {src}")

            path_to_mp3 = os.path.normpath(os.path.join(os.getcwd(), "WebDriverPack/sample.mp3"))
            path_to_wav = os.path.normpath(os.path.join(os.getcwd(), "WebDriverPack/sample.wav"))

            # download the mp3 audio file from the source
            urllib3.request.urlretrieve(src, path_to_mp3)

            # load downloaded mp3 audio file as .wav
            try:
                # as administrator program run required
                sound = pydub.AudioSegment.from_mp3(path_to_mp3)
                sound.export(path_to_wav, format="wav")
                sample_audio = sr.AudioFile(path_to_wav)
            except Exception as e:
                print(Fore.MAGENTA + '[EXCEPT]', Style.RESET_ALL +
                      f' in WebDriver.recaptcha_v2_solver(): \n{str(e)}')
                sys.exit(
                    "[ERR] Please run program as administrator or download ffmpeg manually, "
                    "https://blog.gregzaal.com/how-to-install-ffmpeg-on-windows/"
                )

            # translate audio to text with google voice recognition
            r = sr.Recognizer()
            with sample_audio as source:
                audio = r.record(source)
            key = r.recognize_google(audio)
            print(Fore.YELLOW + '[INFO]', f" Recaptcha Passcode:" + Fore.CYAN + f" {key}")

            # key in results and submit
            sleep(uniform(1.0, 5.0))
            element = self._driver.find_element(By.ID, "audio-response")
            offset = self.get_element_offset(element)
            action = webdriver.ActionChains(self._driver)
            action.move_to_element_with_offset(element, offset['x'], offset['y']).pause(uniform(1.0, 2.0)) \
                .send_keys_to_element(element, key.lower()).send_keys_to_element(element, Keys.ENTER).perform()
            print(Fore.YELLOW + '[INFO]', Style.RESET_ALL + f' Recaptcha Passcode is send')

            # check if recaptcha is passed
            sleep(3)
            src_ = self._driver.find_element(By.ID, "audio-source").get_attribute("src")
            err_ = self._driver.find_element(By.CLASS_NAME, 'rc-audiochallenge-error-message')
            if err_.text.strip() == '' or src_ == src:
                print(Fore.YELLOW + '[INFO]  Recaptcha pass check: ' + Fore.CYAN + 'passed')

                # submit recaptcha result
                if submit:
                    self._submit_bt_click(submit)
                    # form submit check
                    if not submit_check_element:
                        print(Fore.YELLOW + '[INFO]', Fore.MAGENTA +
                              'Form or recaptcha submission is determined by a change in the url, set the validation '
                              'element if the url does not change as a result of the submission, \nor for better '
                              'identification!')
                    if (submit_check_element and self._check_element(submit_check_element)) \
                            or self._driver.current_url != start_url:
                        print(Fore.YELLOW + '[INFO]  Submit check:', Fore.CYAN + f" passed")
                        print(Fore.YELLOW + '[INFO]', Style.RESET_ALL + f" data is submitted")
                    else:
                        print(Fore.YELLOW + '[INFO]', Style.RESET_ALL + f" failed to confirm the data submission")
                        print(Fore.YELLOW + '[INFO]  Submit check:', Fore.CYAN + f" not passed")
                print(Fore.YELLOW + '[INFO]', Style.RESET_ALL + f" Recaptcha is passed")
                return True
            else:
                print(Fore.YELLOW + '[INFO]', Fore.MAGENTA +
                      f' audio-error-message: {err_.text}\n' +
                      Fore.YELLOW + '[INFO]  Pass check: ' + Fore.CYAN + 'not passed, re-listening')
        print(Fore.YELLOW + '[INFO]', Style.RESET_ALL + f" Recaptcha is not passed")
        return False

    def recaptcha_solver_api(self, submit=None,
                             submit_check_element=None):
        start_url = self._driver.current_url

        def submit_check():
            if (submit_check_element and self._check_element(submit_check_element)) \
                    or self._driver.current_url != start_url:
                print(Fore.YELLOW + '[INFO]  Submit check:', Fore.CYAN + f" recaptcha(api) is passed")
                return True
            else:
                print(Fore.YELLOW + '[INFO]', Style.RESET_ALL + f" failed to confirm the data submission")
                print(Fore.YELLOW + '[INFO]  Submit check:', Fore.CYAN + f" recaptcha(api) is not passed")
                return False

        try:
            if submit:
                self._submit_bt_click(submit)
        except Exception as e:
            if self.except_print:
                print(Fore.MAGENTA + '[ERROR]', Style.RESET_ALL + f" Unable to find recaptcha submit. {str(e)}")
            return False
        # check element and text inside after submission
        if submit_check():
            return True
        sleep(3)
        for i in range(10):
            site_key = None
            response_ = None
            try:
                site_key = self._driver.find_element(By.CSS_SELECTOR, 'div.g-recaptcha').get_attribute('data-sitekey')
            except Exception as e:
                if self.except_print:
                    print(Fore.MAGENTA + '[ERROR]', Style.RESET_ALL + f" Unable to find recaptcha site key. {str(e)}")
            print(Fore.YELLOW + '[INFO]', f" Site key:" + Fore.CYAN + f" {site_key}")
            try:
                response_ = self._driver.find_element(By.CSS_SELECTOR, '#g-recaptcha-response')
                self._driver.execute_script("document.getElementById('g-recaptcha-response').style.display = 'block';")
            except Exception as e:
                if self.except_print:
                    print(Fore.MAGENTA + '[ERROR]', Style.RESET_ALL +
                          f" Unable to find recaptcha response input. {str(e)}")
            # get captcha token from api
            key = solve_recaptcha_guru(self._driver.current_url, site_key)
            print(Fore.YELLOW + '[INFO]', f" Recaptcha Token:" + Fore.CYAN + f" {key}")
            if key is not None:
                # send key to input and submit
                action = webdriver.ActionChains(self._driver)
                action.send_keys_to_element(response_, key).perform()
                sleep(uniform(.5, 3))
                if not submit:
                    action = webdriver.ActionChains(self._driver)
                    action.send_keys_to_element(response_, Keys.ENTER).perform()
                else:
                    self._submit_bt_click(submit)
                sleep(3)
                # check element and text inside after submission
                if submit_check():
                    return True
        else:
            print(Fore.YELLOW + '[INFO]', Style.RESET_ALL + f" Failed to pass recaptcha(api)")
            beep(2)
            return False

    def captcha_image_solver_api(self, captcha_image=None,
                                 response=None,
                                 submit=None,
                                 submit_check_element=None):
        start_url = self._driver.current_url
        for i in range(10):
            try:
                src = self.get_element(captcha_image).get_attribute('src')
            except Exception as e:
                if self.except_print:
                    print(Fore.MAGENTA + '[ERROR]', Style.RESET_ALL + f" Unable to find captcha_image. {str(e)}")
                return False
            # open image in new tab
            first_tab = self._driver.current_window_handle
            self._driver.execute_script("window.open('','_blank');")
            new_tab = self._driver.window_handles[1]
            self._driver.switch_to.window(new_tab)
            self.get_page(src)
            # download the image
            if not os.path.exists('Captcha'):
                os.mkdir('Captcha')
            img_path = "Captcha/captcha.png"
            try:
                urllib3.request.urlretrieve(src, img_path)
            except Exception as e:
                if self.except_print:
                    print(Fore.MAGENTA + '[ERROR]', Style.RESET_ALL + f" Unable to download captcha_image. {str(e)}")
                return False
            # close second tab and switch to first tab
            self._driver.close()
            self._driver.switch_to.window(first_tab)

            submit_ = None
            try:
                response_ = self._driver.find_element(*response)
            except Exception as e:
                if self.except_print:
                    print(Fore.MAGENTA + '[ERROR]', Style.RESET_ALL +
                          f" Unable to find captcha response input. {str(e)}")
                return False
            try:
                if submit:
                    submit_ = self._driver.find_element(*submit)
            except Exception as e:
                if self.except_print:
                    print(Fore.MAGENTA + '[ERROR]', Style.RESET_ALL + f" Unable to find captcha submit. {str(e)}")
                return False
            # get captcha key from api
            key = solve_img_captcha_guru(img_path)
            print(Fore.YELLOW + '[INFO]', f" Recaptcha Passcode:" + Fore.CYAN + f" {key}")
            if key is not None:
                # send key to input and submit
                action = webdriver.ActionChains(self._driver)
                action.send_keys_to_element(response_, key).perform()
                sleep(uniform(.5, 3))
                if not submit:
                    action = webdriver.ActionChains(self._driver)
                    action.send_keys_to_element(response_, Keys.ENTER).perform()
                else:
                    submit_.click()
                sleep(1)
                # check element and text inside after submission
                if (submit_check_element and self._check_element(submit_check_element)) \
                        or self._driver.current_url != start_url:
                    print(Fore.YELLOW + '[INFO]  Submit check:', Fore.CYAN + f" image captcha is passed")
                    return True
                else:
                    print(Fore.YELLOW + '[INFO]', Style.RESET_ALL + f" failed to confirm the data submission")
                    print(Fore.YELLOW + '[INFO]  Submit check:', Fore.CYAN + f" image captcha is not passed")
        else:
            print(Fore.YELLOW + '[INFO]', Style.RESET_ALL + f" Failed to pass image captcha")
            beep(2)
            return False

    # def save_img(self, src: str, root_folder: str = 'result data', project_folder: str = None, folder: str = 'images',
    #              max_size: int = None):
    #     """Saves the image and returns the file path"""
    #     path = super().save_img(src, root_folder, project_folder, folder)
    #     urllib3.request.urlretrieve(src, path)
    #     if max_size:
    #         resize_image(path, max_size)
    #     return path

    def print_msg(self, location: str = None, msg: str = '', exception: bool = False, stream: int = None):
        if exception and self.except_print:
            print_exception_msg(msg, stream)
        else:
            print_info_msg(msg, stream)

    def download_file_wait(self, download_bt: WebElement, dist_path: str = None, wait: int = 30):
        """waits for the file to download and moves it to the specified folder"""
        path = os.getcwd() + f'/Downloads/{self.stream}'
        files_ = os.listdir(path)
        download_bt.click()
        for i in range(wait):
            check, files = True, os.listdir(path)
            if len(files_) < len(files):
                for file in files:
                    if '.crdownload' in file or '.tmp' in file:
                        check = False
                        break
                if check:
                    break
            sleep(1)
        print('download complete')
        file_name_ = max([path + "\\" + f for f in os.listdir(path)], key=os.path.getctime)
        print(f'downloaded file: {file_name_}')
        if dist_path:
            shutil.move(file_name_, os.path.join(os.getcwd(), dist_path))


