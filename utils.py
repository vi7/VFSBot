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

# def break_captcha():
#         img = cv2.imread('captcha.png')
#         image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#         se = cv2.getStructuringElement(cv2.MORPH_RECT, (8,8))
#         bg = cv2.morphologyEx(image, cv2.MORPH_DILATE, se)
#         out_gray = cv2.divide(image, bg, scale=255)
#         out_binary = cv2.threshold(out_gray, 0, 255, cv2.THRESH_OTSU )[1]

#         captcha = pytesseract.image_to_string(out_binary, config='--psm 13 -c tessedit_char_whitelist=ABCDEFGHIJKLMNPQRSTUVWYZ')
#         denoised_captcha =  re.sub('[\W_]+', '', captcha).strip()

#         return denoised_captcha

def resolve_captcha(driver):
    path = os.path.abspath(os.getcwd())

    frames = driver.find_elements(By.TAG_NAME, 'iframe')
    driver.switch_to.frame(frames[0])
    sleep(randint(2, 4))

    driver.find_element(By.CLASS_NAME, 'recaptcha-checkbox-border').click()

    driver.switch_to.default_content()

    frames = driver.find_element(By.XPATH,
        '/html/body/div[2]/div[4]').find_elements(By.TAG_NAME, 'iframe')

    sleep(randint(2, 4))

    driver.switch_to.default_content()

    frames = driver.find_elements(By.TAG_NAME, 'iframe')

    driver.switch_to.frame(frames[-1])

    driver.find_element(By.ID, 'recaptcha-audio-button').click()

    driver.switch_to.default_content()

    frames = driver.find_elements(By.TAG_NAME, 'iframe')

    driver.switch_to.frame(frames[-1])

    sleep(randint(2, 4))

    driver.find_element(By.XPATH, '/html/body/div/div/div[3]/div/button').click()

    try:
        src = driver.find_element(By.ID, 'audio-source').get_attribute("src")
        print(src)
        urllib.request.urlretrieve(src, path+"\\audio.mp3")

        sound = pydub.AudioSegment.from_mp3(
            path+"\\audio.mp3").export(path+"\\audio.wav", format="wav")

        recognizer = Recognizer()

        recaptcha_audio = AudioFile(path+"\\audio.wav")

        with recaptcha_audio as source:
            audio = recognizer.record(source)

        text = recognizer.recognize_google(audio, language="en-GB")

        print("captcha text: {}".format(text))

        inputfield = driver.find_element(By.ID, 'audio-response')
        inputfield.send_keys(text.lower())
        inputfield.send_keys(Keys.ENTER)
        sleep(10)

        print("Login captcha resolved successfully")

    except NameError:
        print("reCaptcha resolver FAILED!")
        print(NameError)
        # driver.quit()
