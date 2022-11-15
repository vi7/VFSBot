import time
import threading
from random import randint
from utils import *
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from telegram.ext.updater import Updater
from telegram.ext.commandhandler import CommandHandler
from configparser import ConfigParser
import undetected_chromedriver as uc
from datetime import datetime

class VFSBot:
    def __init__(self):
        path = os.path.abspath(os.getcwd())

        self.config = ConfigParser()
        self.config.read('config.ini')

        self.url = self.config.get('VFS', 'url')
        self.email_str = self.config.get('VFS', 'email')
        self.pwd_str = self.config.get('VFS', 'password')
        self.interval = self.config.getint('DEFAULT', 'interval')
        self.channel_id = self.config.get('TELEGRAM', 'channel_id')
        self.quit_evt = threading.Event()
        token = self.config.get('TELEGRAM', 'auth_token')
        admin_ids = list(map(int, self.config.get('TELEGRAM', 'admin_ids').split(" ")))

        updater = Updater(token, use_context=True)

        dp = updater.dispatcher

        dp.add_handler(AdminHandler(admin_ids))
        dp.add_handler(CommandHandler("start", self.start))
        dp.add_handler(CommandHandler("help", self.help))
        dp.add_handler(CommandHandler("quit", self.quit))

        updater.start_polling()
        updater.idle()

    def login(self, update, context):
        self.browser.get((self.url))
        time.sleep(2)
        queue_msg_sent = False

        while True:
            if self.quit_evt.is_set():
                return
            # if "You are now in line." in self.browser.page_source:
            if "Please note that improvements" in self.browser.page_source:
                if not queue_msg_sent:
                    update.message.reply_text("You are now in queue.")
                    queue_msg_sent = True
                time.sleep(10)
            else:
                break

        WebDriverWait(self.browser, 60).until(EC.presence_of_element_located((By.NAME, 'EmailId')))

        self.browser.find_element(by=By.NAME, value='EmailId').send_keys(self.email_str)
        self.browser.find_element(by=By.NAME, value='Password').send_keys(self.pwd_str)

        resolve_captcha(self.browser)

        time.sleep(randint(1, 3))
        self.browser.find_element(by=By.ID, value='btnSubmit').click()

        if "Schedule Appointment" in self.browser.page_source:
            update.message.reply_text("Successfully logged in!")
            while True:
                if self.quit_evt.is_set():
                    return
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
            if self.quit_evt.is_set():
                return
            try:
                self.open_browser()
                self.login(update, context)
            except Exception as e:
                print("Error happened:\n {}\nException type: {}\n\nRestarting session\n".format(
                    str(e).split("\n")[0], type(e)
                    ))
                self.browser.quit()
                self.open_browser()
                continue

    def open_browser(self):
        options = webdriver.ChromeOptions()
        options.add_argument("start-maximized")
        self.browser = uc.Chrome(options=options,
                 executable_path=r'chromedriver')

    def help(self, update, context):
        update.message.reply_text("This is a VFS appointment bot!\nPress /start to begin.")

    def start(self, update, context):
        self.quit_evt.clear()
        try:
            self.browser.close()
        except:
            pass
        update.message.reply_text('Logging in...')

        self.thr = threading.Thread(target=self.login_helper, args=(update, context))
        self.thr.start()


    def quit(self, update, context):
        self.quit_evt.set()
        try:
            self.browser.quit()
        except Exception as err:
            print(f"The following error occured while quitting {err=}, {type(err)=}")
            update.message.reply_text("Unexpected error while quitting!")
            pass
        else:
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
        print("{} Checking appointment.".format(datetime.now()))
        time.sleep(randint(1, 3))

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

        # Option 7 for Minsk
        self.browser.find_element(by=By.XPATH, value='//*[@id="LocationId"]/option[7]').click()
        if self.check_errors():
            raise WebError
        time.sleep(randint(3, 6))

        if "There are no open seats available for selected center - Poland Visa Application Center-Minsk" in self.browser.page_source:

            records = open("record.txt", "r+")
            last_date = records.readlines()[-1]

            if last_date != '0':
                context.bot.send_message(chat_id=self.channel_id,
                                         text="There are no appointments for city available right now.")
                records.write('\n' + '0')
                records.close
            return True

        else:
            select = Select(self.browser.find_element(by=By.XPATH, value='//*[@id="VisaCategoryId"]'))
            # value 301 - Schengen C-visa, value 2659 for indian Schengen visa
            select.select_by_value('301')
            time.sleep(randint(3, 6))

            # todo check msg
            if "There are no open seats available for selected center - Poland Visa Application Center-Minsk" in self.browser.page_source:

                records = open("record.txt", "r+")
                last_date = records.readlines()[-1]

                if last_date != '0':
                    context.bot.send_message(chat_id=self.channel_id,
                                         text="There are no appointments for visa type available right now.")
                    records.write('\n' + '0')
                    records.close
                return True

            else:

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

                time.sleep(randint(2, 4))
                self.browser.find_element(by=By.ID, value='btnContinue').click()
                self.process_user(update, context)

                return True

    def process_user(self, update, context): 

        WebDriverWait(self.browser, 4).until(EC.presence_of_element_located((By.XPATH, '//*[@id="ApplicantListForm"]')))
        update.message.reply_text("Trying to add customer..")

        time.sleep(randint(2, 4))
        self.browser.find_element(by=By.XPATH, value='/html/body/div[2]/div[1]/div[3]/div[3]/a').click()

        WebDriverWait(self.browser, 4).until(EC.presence_of_element_located((By.ID, 'PassportNumber')))
        time.sleep(randint(2, 4))

        self.browser.find_element(by=By.ID, value='PassportNumber').send_keys(self.config.get('USER', 'passport_number'))
        self.browser.find_element(by=By.ID, value='DateOfBirth').send_keys(self.config.get('USER', 'date_of_birth'))
        self.browser.find_element(by=By.ID, value='PassportExpiryDate').send_keys(self.config.get('USER', 'passport_exp_date'))  
        self.browser.find_element(by=By.XPATH, value='//*[@id="NationalityId"]/option[20]').click()    

        self.browser.find_element(by=By.ID, value='FirstName').clear()
        self.browser.find_element(by=By.ID, value='FirstName').send_keys(self.config.get('USER', 'first_name'))
        self.browser.find_element(by=By.ID, value='LastName').clear()
        self.browser.find_element(by=By.ID, value='LastName').send_keys(self.config.get('USER', 'last_name'))
        self.browser.find_element(by=By.XPATH, value='//*[@id="GenderId"]/option[2]').click()    

        self.browser.find_element(by=By.ID, value='Mobile').clear() 
        self.browser.find_element(by=By.ID, value='Mobile').send_keys(self.config.get('USER', 'mobile_number')) 

        self.browser.find_element(by=By.ID, value='validateEmailId').clear()
        self.browser.find_element(by=By.ID, value='validateEmailId').send_keys(self.config.get('USER', 'email')) 

        time.sleep(15)

        # self.browser.find_element(by=By.ID, value='submitbuttonId').click()


if __name__ == '__main__':
    VFSbot = VFSBot()
