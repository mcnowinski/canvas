#!/usr/bin/python3

"""
DESCRIPTION: This script logs into a canvas course and scrapes the submitted assignments.
INPUT(S):
    - Canvas username
    - Canvas password
    - Canvas course URL
"""

import sys
import os
import logging
import argparse
import re
import json
from seleniumwire import webdriver
from seleniumwire.utils import decode
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

#
# logging
#
logging.basicConfig(
    level=logging.WARN,
    format='%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s',
    handlers=[
        logging.FileHandler('canvas_scrape_submitted.log'),
        logging.StreamHandler()
    ])
logger = logging.getLogger('canvas_scrape_submitted')

#
# command line
#
parser = argparse.ArgumentParser()
parser.add_argument('username', help='Username')
parser.add_argument('password', help='Password')
parser.add_argument('course_url', help='Course URL')
args = parser.parse_args()
# get canvas course URL from the command line
course_url = args.course_url #e.g., 'https://canvas.vt.edu/courses/158608'
# get credentials from command line
username = args.username
password = args.password

#
# Selenium
#
# initialize the Chrome driver
# NOTE: install a chromedriver version that matches your computer's version of Chrome (https://chromedriver.chromium.org/downloads)
driver = webdriver.Chrome('chromedriver')


#
# 1. Log on to Canvas course page
#
driver.get(course_url) # go to course URL
driver.find_element(By.ID, 'username').send_keys(username) # enter username
driver.find_element(By.ID, 'password').send_keys(password) # enter password
driver.find_element(By.NAME, '_eventId_proceed').click() # click login button
# two-factor authentication (2FA)
# switch to 2FA page iframe
driver.switch_to.frame(driver.find_element(By.XPATH, "//iframe[@id='duo_iframe']"))
# click Send Me a Push button
driver.find_element(By.XPATH, "//button[contains(text(), 'Send Me a Push')]").click()

#
# 2. Go to Canvas New Analytics tool
# a. Get the session_id (for https) and context_id (for LTI)
#
# wait for 2FA to log us on, then click New Analytics from the left menu
WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'New Analytics')]"))).click()
# switch to tools iframe
driver.switch_to.frame(driver.find_element(By.XPATH, "//iframe[@id='tool_content']"))
# scrape a graphql request to get session-id, contextId, and tcGuid
found_graphql_query = False
session_id = None
context_id = None
tc_guid = None
for request in driver.requests:
    if request.response and re.search(r'graphql$', request.url):
        session_id = request.headers['session-id']
        json_payload = json.loads(decode(request.body, request.headers.get('Content-Encoding', 'identity')))
        context_id = json_payload['variables']['contextId']
        tc_guid = json_payload['variables']['tcGuid']
        found_graphql_query = True
        break
        
if not found_graphql_query:
    sys.exit('Error. Could not scrape required parameters from URL.')
        
## click Reports tab
#driver.find_element(By.ID, 'tab-reports').click()
# run Roster Report
#driver.find_element(By.XPATH, "//button[@data-testid='run-report-roster']").click()
