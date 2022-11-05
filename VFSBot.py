import threading
import pydub
import urllib
import os
from time import sleep
from random import randint
from utils import *
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from telegram.ext.updater import Updater
from telegram.ext.commandhandler import CommandHandler
from configparser import ConfigParser
import undetected_chromedriver as uc
from speech_recognition import Recognizer, AudioFile

class VFSBot:
    def __init__(self):
        path = os.path.abspath(os.getcwd())

        config = ConfigParser()
        config.read('config.ini')

        self.url = config.get('VFS', 'url')
        self.email_str = config.get('VFS', 'email')
        self.pwd_str = config.get('VFS', 'password')
        self.interval = config.getint('DEFAULT', 'interval')
        self.channel_id = config.get('TELEGRAM', 'channel_id')
        token = config.get('TELEGRAM', 'auth_token')
        admin_ids = list(map(int, config.get('TELEGRAM', 'admin_ids').split(" ")))

        updater = Updater(token, use_context=True)

        self.options = webdriver.ChromeOptions()
        self.options.add_argument("start-maximized")

        dp = updater.dispatcher

        dp.add_handler(AdminHandler(admin_ids))
        dp.add_handler(CommandHandler("start", self.start))
        dp.add_handler(CommandHandler("help", self.help))
        dp.add_handler(CommandHandler("quit", self.quit))

        updater.start_polling()
        updater.idle()

    def login(self, update, context):
        self.browser.get((self.url))

        if "You are now in line." in self.browser.page_source:
           update.message.reply_text("You are now in queue.")

        WebDriverWait(self.browser, 600).until(EC.presence_of_element_located((By.NAME, 'EmailId')))

        self.browser.find_element(by=By.NAME, value='EmailId').send_keys(self.email_str)
        self.browser.find_element(by=By.NAME, value='Password').send_keys(self.pwd_str)


        captcha_img = self.browser.find_element(by=By.ID, value='CaptchaImage')

        self.captcha_filename = 'captcha.png'
        with open(self.captcha_filename, 'wb') as file:
            file.write(captcha_img.screenshot_as_png)

        captcha = break_captcha()

        self.browser.find_element(by=By.NAME, value='CaptchaInputText').send_keys(captcha)
        time.sleep(randint(1, 3))
        self.browser.find_element(by=By.ID, value='btnSubmit').click()

        if "Reschedule Appointment" in self.browser.page_source:
            update.message.reply_text("Successfully logged in!")
            while True:
                try:
                    self.check_appointment(update, context)
                except WebError:
                    update.message.reply_text("An error has occured.\nTrying again.")
                    raise WebError
                except Offline:
                    update.message.reply_text("Downloaded offline version. Trying again.")
                    continue
                except:
                    update.message.reply_text("An error has occured. \nTrying again.")
                    raise WebError
                time.sleep(self.interval)
        elif "Your account has been locked, please login after 2 minutes." in self.browser.page_source:
           update.message.reply_text("Account locked.\nPlease wait 2 minutes.")
           time.sleep(randint(121, 125))
           return
        elif "The verification words are incorrect." in self.browser.page_source:
           #update.message.reply_text("Incorrect captcha. \nTrying again.")
           return
        else:
            update.message.reply_text("An error has occured. \nTrying again.")
            #self.browser.find_element(by=By.XPATH, value='//*[@id="logoutForm"]/a').click()
            raise WebError


    def login_helper(self, update, context):
        while True:
            try:
                self.login(update, context)
            except:
                self.browser.quit()
                self.open_browser()
                continue

    def open_browser(self):
        self.browser = uc.Chrome(options=self.options,
                 executable_path=r'chromedriver')

    def help(self, update, context):
        update.message.reply_text("This is a VFS appointment bot!\nPress /start to begin.")

    def start(self, update, context):
        try:
            self.browser.close()
        except:
                pass
        update.message.reply_text('Logging in...')
        self.open_browser()

        self.thr = threading.Thread(target=self.login_helper, args=(update, context))
        self.thr.start()


    def quit(self, update, context):
        try:
            self.browser.quit()
            self.thr.terminate()
        except:
            pass
        update.message.reply_text("Quit successfully.")

    def check_errors(self):
        if "Server Error in '/Global-Appointment' Application." in self.browser.page_source:
            return True
        elif "Cloudflare" in self.browser.page_source:
            return True
        elif "Sorry, looks like you were going too fast." in self.browser.page_source:
            return True
        elif "Session expired." in self.browser.page_source:
            return True
        elif "Sorry, looks like you were going too fast." in self.browser.page_source:
            return True

    def check_offline(self):
        if "offline" in self.browser.page_source:
            return True

    def check_appointment(self, update, context):
        time.sleep(randint(3, 6))

        self.browser.find_element(by=By.XPATH,
                                value='//*[@id="Accordion1"]/div/div[2]/div/ul/li[1]/a').click()
        if self.check_errors():
            raise WebError
        if self.check_offline():
            raise Offline

        WebDriverWait(self.browser, 100).until(EC.presence_of_element_located((
            By.XPATH, '//*[@id="LocationId"]')))

        self.browser.find_element(by=By.XPATH, value='//*[@id="LocationId"]').click()
        if self.check_errors():
             raise WebError
        time.sleep(randint(3, 6))


        self.browser.find_element(by=By.XPATH, value='//*[@id="LocationId"]/option[2]').click()
        if self.check_errors():
            raise WebError

        time.sleep(randint(3, 6))


        if "There are no open seats available for selected center - Belgium Long Term Visa Application Center-Tehran" in self.browser.page_source:
            #update.message.reply_text("There are no appointments available.")
            records = open("record.txt", "r+")
            last_date = records.readlines()[-1]

            if last_date != '0':
                context.bot.send_message(chat_id=self.channel_id,
                                         text="There are no appointments available right now.")
                records.write('\n' + '0')
                records.close
            return True

        else:
            select = Select(self.browser.find_element(by=By.XPATH, value='//*[@id="VisaCategoryId"]'))
            select.select_by_value('1314')

            WebDriverWait(self.browser, 100).until(EC.presence_of_element_located((
                By.XPATH, '//*[@id="dvEarliestDateLnk"]')))

            time.sleep(randint(2, 4))
            new_date = self.browser.find_element(by=By.XPATH,
                           value='//*[@id="lblDate"]').get_attribute('innerHTML')

            records = open("record.txt", "r+")
            last_date = records.readlines()[-1]

            if new_date != last_date and len(new_date) > 0:
                context.bot.send_message(chat_id=self.channel_id,
                                         text=f"Appointment available on {new_date}.")
                records.write('\n' + new_date)
                records.close()
            #update.message.reply_text("Checked!", disable_notification=True)
            return True


if __name__ == '__main__':
    VFSbot = VFSBot()
