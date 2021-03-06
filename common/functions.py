import time
from abc import ABCMeta
from abc import abstractmethod
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
import telegram


# List of FIBO(Front-In, Back-Out), kind of queue
class ListFIBO:
    def __init__(self, items, maxsize):
        self.maxsize = maxsize
        self.list_fibo = list(items[:maxsize])

    def put(self, item):
        if len(self.list_fibo) == self.maxsize:
            self.list_fibo.pop()
        self.list_fibo.insert(0, item)

    def have(self, item):
        return item in self.list_fibo


class TelegramBot:
    def __init__(self, token, chat_ids):
        # Connect to the telegram bot
        for _ in range(10):
            try:
                bot = telegram.Bot(token=token)
                break
            except telegram.error.TimedOut as error:
                print(error)
                print("    at TelegramBot()")
                time.sleep(1)

        # Set the telegram bot and chat id set
        self.bot = bot
        self.chat_ids = chat_ids | self.get_chat_ids()

    # Get the present list of non-duplicate recipients
    # - pure function
    def get_chat_ids(self):
        # Get the recent chat id list from the bot
        for _ in range(10):
            try:
                updates = self.bot.get_updates(timeout=10)
                break
            except telegram.error.NetworkError as error:
                print(error)
                print("    at get_chat_ids()")
                time.sleep(1)

        # Exclude duplicate chat id
        return {update.message.chat.id for update in updates}

    # Send the message to the telegram bot
    def send_message(self, message):
        # Add new recipients if exist
        self.chat_ids |= self.get_chat_ids()

        message_sent = False
        sent_chat_id = []

        # Send the message to all users in chat_id_set
        for chat_id in self.chat_ids:
            for _ in range(10):
                try:
                    self.bot.send_message(chat_id=chat_id, text=message)
                    message_sent = True
                    sent_chat_id.append(chat_id)
                    break
                except telegram.error.NetworkError as error:
                    print(error)
                    print("    at send_message()")
                    time.sleep(1)

        if message_sent:
            print("The message has sent to", sent_chat_id, message.replace("\n", " ")[:35], "...")
        else:
            print("Failed to send message because there was no recipient")

        return message_sent


class Chrome(metaclass=ABCMeta):
    def __init__(self, wait_sec=10):
        # Setting chrome options
        print("Initialize the chrome webdriver...")
        options = webdriver.ChromeOptions()
        options.add_argument("headless")
        options.add_argument("disable-gpu")
        # options.add_argument("no-sandbox")
        options.add_argument("disable-dev-shm-usage")
        options.add_argument("window-size=1920x1080")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36"
        )
        options.add_argument("lang=ko_KR")
        options.add_argument("log-level=2")
        prefs = {
            "profile.default_content_setting_values": {
                "cookies": 1,
                "images": 2,
                "plugins": 2,
                "popups": 2,
                "geolocation": 2,
                "notifications": 2,
                "auto_select_certificate": 2,
                "fullscreen": 2,
                "mouselock": 2,
                "mixed_script": 2,
                "media_stream": 2,
                "media_stream_mic": 2,
                "media_stream_camera": 2,
                "protocol_handlers": 2,
                "ppapi_broker": 2,
                "automatic_downloads": 2,
                "midi_sysex": 2,
                "push_messaging": 2,
                "ssl_cert_decisions": 2,
                "metro_switch_to_desktop": 2,
                "protected_media_identifier": 2,
                "app_banner": 2,
                "site_engagement": 2,
                "durable_storage": 2,
            }
        }
        options.add_experimental_option("prefs", prefs)

        # Initialize chrome driver
        self.driver = webdriver.Chrome("../chromedriver", options=options)
        self.driver.implicitly_wait(wait_sec)
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'plugins', {get: function() {return[1, 2, 3, 4, 5]}})"
        )
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'languages', {get: function() {return ['ko-KR', 'ko']}})"
        )
        self.driver.execute_script(
            "const getParameter = WebGLRenderingContext.getParameter;WebGLRenderingContext.prototype.getParameter = function(parameter) {if (parameter === 37445) {return 'NVIDIA Corporation'} if (parameter === 37446) {return 'NVIDIA GeForce GTX 980 Ti OpenGL Engine';}return getParameter(parameter);};"
        )

    # Return a list of the bs4 elements if exists, else return a empty list
    # - return type: bs4.element.ResultSet
    def get_bs4_elements(self, css_selector, wait_sec=10):
        for _ in range(wait_sec):
            try:
                elements = BeautifulSoup(self.driver.page_source, "html.parser").select(css_selector)
                if elements:
                    return elements
            except WebDriverException as error:
                print(error)
                print("    at get_bs4_elements()")
            time.sleep(1)

        print("No elements")
        return elements

    # Return the bs4 element if exists, else return None
    # - return type: bs4.element.Tag or None
    def get_bs4_element(self, css_selector, wait_sec=10):
        for _ in range(wait_sec):
            try:
                html = self.driver.page_source.replace("<br>", "\n")  # Read <br> tag as new line
                element = BeautifulSoup(html, "html.parser").select_one(css_selector)
                if element:
                    return element
            except WebDriverException as error:
                print(error)
                print("    at get_bs4_element()")
            time.sleep(1)

        print("No element")
        return element

    # Request GET to given url
    def go_to_page(self, url):
        try:
            self.driver.get(url)
            return True
        except WebDriverException as error:
            print(error, end="")
            print("    at go_to_page()")
            return False

