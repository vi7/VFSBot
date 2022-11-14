#import cv2
# import re
#import pytesseract
import pydub
import urllib
import os
from time import sleep
from random import randint
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException
from speech_recognition import Recognizer, AudioFile
import telegram
from telegram.ext import Handler

# pytesseract.pytesseract.tesseract_cmd = 'tesseract'

class WebError(Exception):
    pass

class Offline(Exception):
    pass

class AdminHandler(Handler):
    def __init__(self, admin_ids):
        super().__init__(self.cb)
        self.admin_ids = admin_ids

    def cb(self, update: telegram.Update, context):
        update.message.reply_text('Unauthorized access!')

    def check_update(self, update: telegram.update.Update):
        if update.message is None or update.message.from_user.id not in self.admin_ids:
            return True

        return False

def resolve_captcha(driver):
    path = os.path.abspath(os.getcwd())
    update = telegram.Update
    captcha_xpath = "//iframe[@title='reCAPTCHA']"
    captcha_audio_lang = 'en-GB'

    print('Waiting for captcha iframe')
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.XPATH, captcha_xpath))
    )
    frame = driver.find_element(By.XPATH, captcha_xpath)
    driver.switch_to.frame(frame)
    sleep(randint(2, 4))

    driver.find_element(By.CLASS_NAME, 'recaptcha-checkbox-border').click()
    driver.switch_to.default_content()

    frames = driver.find_element(By.XPATH,
        '/html/body/div[4]/div[4]').find_elements(By.TAG_NAME, 'iframe')
    sleep(randint(2, 4))
    driver.switch_to.frame(frames[0])

    try:
        driver.find_element(By.ID, 'recaptcha-audio-button').click()
    except ElementClickInterceptedException:
        print('No captcha resolution needed')
        driver.switch_to.default_content()
        return
    driver.switch_to.default_content()

    frames = driver.find_element(By.XPATH,
        '/html/body/div[4]/div[4]').find_elements(By.TAG_NAME, 'iframe')
    driver.switch_to.frame(frames[0])
    sleep(randint(2, 4))

    driver.find_element(By.XPATH, '/html/body/div/div/div[3]/div/button').click()

    try:
        src = driver.find_element(By.ID, 'audio-source').get_attribute("src")
        # print("Captcha url: {}".format(src))
        urllib.request.urlretrieve(src, path+"\\audio.mp3")

        sound = pydub.AudioSegment.from_mp3(
            path+"\\audio.mp3").export(path+"\\audio.wav", format="wav")

        recognizer = Recognizer()
        recaptcha_audio = AudioFile(path+"\\audio.wav")
        with recaptcha_audio as source:
            audio = recognizer.record(source)
        text = recognizer.recognize_google(audio, language=captcha_audio_lang)
        # print("captcha text: {}".format(text))

        inputfield = driver.find_element(By.ID, 'audio-response')
        inputfield.send_keys(text.lower())
        inputfield.send_keys(Keys.ENTER)
        sleep(10)

        print("Login captcha resolved successfully")

        driver.switch_to.default_content()

    except NameError:
        print("Captcha resolver FAILED!")
        update.message.reply_text('Captcha resolver FAILED!')
        print(NameError)
        # driver.quit()
