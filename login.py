#!/usr/bin/python3

"""
DESCRIPTION: This script performs a Canvas login.
INPUT(S):
    - Username and password.
"""

import sys
import os
import logging
import argparse
from seleniumwire import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


# configure logging
logging.basicConfig(
    level=logging.WARN,
    format='%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s',
    handlers=[
        logging.FileHandler('login.log'),
        logging.StreamHandler()
    ])
logger = logging.getLogger('login')

parser = argparse.ArgumentParser()
parser.add_argument('username', help='Username')
parser.add_argument('password', help='Password')
args = parser.parse_args()

# Canvas URL
canvas_course_url = 'https://canvas.vt.edu/courses/158608'

# get credentials from command line
username = args.username
password = args.password

# initialize the Chrome driver
# install a chromedriver version that matches your computer's version of Chrome (https://chromedriver.chromium.org/downloads)
driver = webdriver.Chrome('chromedriver')

# head to Canvas course page
driver.get(canvas_course_url)
# find username/email field and send the username itself to the input field
driver.find_element(By.ID, 'username').send_keys(username)
# find password input field and insert password as well
driver.find_element(By.ID, 'password').send_keys(password)
# click login button
driver.find_element(By.NAME, '_eventId_proceed').click()

# complete the two-factor authentication
# switch to main iframe
driver.switch_to.frame(driver.find_element(By.XPATH, "//iframe[@id='duo_iframe']"))
# click Push button when ready
driver.find_element(By.XPATH, "//button[contains(text(), 'Send Me a Push')]").click()

# wait for 2FA to log us on, then click New Analytics
WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'New Analytics')]"))) #.click()
## switch to tools iframe
#driver.switch_to.frame(driver.find_element(By.XPATH, "//iframe[@id='tool_content']"))
## click Reports
#driver.find_element(By.ID, 'tab-reports').click()
## Access requests via the `requests` attribute
for request in driver.requests:
    if request.response:
        print(
            request.url,
            request.response.status_code,
            request.response.headers['Content-Type']
        )
# run Roster Report
#driver.find_element(By.XPATH, "//button[@data-testid='run-report-roster']").click()
