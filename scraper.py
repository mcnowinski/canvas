#!/usr/bin/python3

"""
DESCRIPTION: This script logs into a canvas course and scrapes the submitted assignments.
INPUT(S):
    - Canvas username
    - Canvas password
    - Canvas course URL
"""

import sys
import logging
import argparse
import re
import json
import time
# automate Chrome
logging.getLogger('seleniumwire').setLevel(logging.ERROR)
from seleniumwire import webdriver
from seleniumwire.utils import decode
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
# csv output
import pandas as pd

#
# logging
#
logging.basicConfig(
    level=logging.INFO,
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
course_url = args.course_url  # e.g., 'https://canvas.vt.edu/courses/123456'
# get credentials from command line
username = args.username
password = args.password

#
# Selenium
#
# initialize the Chrome driver
# NOTE: install a chromedriver version that matches your computer's version of Chrome (https://chromedriver.chromium.org/downloads)
options = webdriver.ChromeOptions() 
options.add_experimental_option('excludeSwitches', ['enable-logging']) # to supress the error messages/logs
options.add_argument("--headless") # headless
driver = webdriver.Chrome(options=options, executable_path=r'chromedriver.exe')

datetime_headers = ['lastParticipationTime', 'lastPageviewTime', 'lastLoggedOut', 'dueDate', '.date']
def reformat(name, x):
    """apply any special value re-formatting"""

    # change datetime fields to Y-m-d H:M:S
    if re.search(r'|'.join(datetime_headers), name) and isinstance(x, int):
        return time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(x/1000.0))

    return x

def flatten_json(nested_json, exclude=['']):
    """Flatten json object with nested keys into a single level.
        Args:
            nested_json: A nested json object.
            exclude: Keys to exclude from output.
        Returns:
            The flattened json object if successful, None otherwise.
        #
        # the original version of this function is from
        # https://stackoverflow.com/questions/52795561/flattening-nested-json-in-pandas-data-frame
        #            
    """
    out = {}

    # recursively flatten JSON
    def flatten(x, name='', exclude=exclude):
        if type(x) is dict:
            for a in x:
                if a not in exclude:
                    flatten(x[a], name + a + '.')
        elif type(x) is list:
            i = 0
            for a in x:
                flatten(a, name + str(i) + '.')
                i += 1
        else:
            out[name[:-1]] = reformat(name[:-1], x)

    flatten(nested_json)
    return out


def main():
    """ the main function """
    #
    # 1. Log on to Canvas course page
    #
    logger.info('Logging on to %s...'%course_url)
    driver.get(course_url)  # go to course URL
    driver.find_element(By.ID, 'username').send_keys(
        username)  # enter username
    driver.find_element(By.ID, 'password').send_keys(
        password)  # enter password
    # click login button
    driver.find_element(By.NAME, '_eventId_proceed').click()
    # two-factor authentication (2FA)
    # switch to 2FA page iframe
    driver.switch_to.frame(driver.find_element(
        By.XPATH, "//iframe[@id='duo_iframe']"))
    # click Send Me a Push button
    driver.find_element(
        By.XPATH, "//button[contains(text(), 'Send Me a Push')]").click()

    #
    # 2. Go to Canvas New Analytics tool
    #
    # wait for 2FA to log us on, then click New Analytics from the left menu
    logger.info('Waiting for 2-Factor Authentication...')
    WebDriverWait(driver, 60).until(EC.element_to_be_clickable(
        (By.XPATH, "//a[contains(text(),'New Analytics')]"))).click()
    logger.info('Authenticated!')
    #
    # 3. Get student and assignment data
    #
    # see additional notes at the bottom of this script

    # find the CourseDetail graphql request
    logger.info('Scraping student and assignment data...')
    got_filter_query = False
    for request in driver.requests:
        if re.search(r'graphql$', request.url) and request.response:
            try:
                json_request = json.loads(decode(request.body, request.headers.get(
                    'Content-Encoding', 'identity')))  # get the request
                # is it a CourseDetail query?
                if json_request['operationName'] == 'CourseDetail':
                    json_response = json.loads(decode(request.response.body, request.response.headers.get(
                        'Content-Encoding', 'identity')))  # get the response
                    got_filter_query = True
                    break
            except Exception as e:  # ooops!
                logger.error('Invalid GraphQL JSON response (%s).' % e)
                sys.exit()

    # did we get the info we needed?
    if not got_filter_query:
        logger.error('GraphQL CourseDetail request not found.' % e)
        sys.exit()

    exclude = ['__typename', 'missing', 'avatarURL', 'cursor']
    # extract list of students, list of assignments, and student assignment activity
    students = pd.DataFrame([flatten_json(
        x, exclude) for x in json_response['data']['course']['studentInCourseConnection']['edges']])
    assignments = pd.DataFrame([flatten_json(
        x, exclude) for x in json_response['data']['course']['assignmentForCourseConnection']['edges']])
    student_assignment_activity = pd.DataFrame([flatten_json(
        x, exclude) for x in json_response['data']['course']['assignmentsForStudents']])
    #course = json_response['data']['course']

    # write to .csv file
    logger.info('Writing student data to students.csv...')
    students.to_csv('students.csv')
    logger.info('Writing assignment data to assignments.csv...')    
    assignments.to_csv('assignments.csv')
    logger.info('Writing student assignment activity to student_assignment_activity.csv...')        
    student_assignment_activity.to_csv('student_assignment_activity.csv')

    # close Chrome
    driver.quit()

    logger.info('Scraping complete!')


if __name__ == '__main__':
    main()

#
# notes
#
# we are interested in the CourseDetail graphql request that looks like this:
"""
{
    "operationName": "CourseDetail",
    "variables": {
        "contextId": "7c82cf32d76cd2933b7516aa68c2b8686d6754af",
        "tcGuid": "yDz0MxxBs02YM08vCb8fQ85ISbDXw62vLT6KiA6s:canvas-lms"
    },
    "query": ""
}
"""
# this request produces a response that looks like this:
"""
{
    "data": {
        "course": {
            "contextId": "7c82cf32d76cd2933b7516aa68c2b8686d6754af",
            "tcGuid": "yDz0MxxBs02YM08vCb8fQ85ISbDXw62vLT6KiA6s:canvas-lms",
            "courseId": "158608",
            "name": "Eng Analysis Numerical Methods (Fall 2022)",
            "startDate": null,
            "etlStart": 1663439548924,
            "updatedAt": 1663345375814,
            "mean": 95.47155038759685,
            "sections": [
                {
                    "id": "45110000000176720",
                    "name": "ME_2004_90432_202209",
                    "hasStudents": true,
                    "__typename": "Section"
                },
                ...
            ],
            "assignmentForCourseConnection": {
                "edges": [
                    {
                        "assignment": {
                            "id": "45110000001559394",
                            "name": "Recitation 1",
                            "stats": {
                                "min": 0,
                                "mean": 97.63779527559055,
                                "max": 100,
                                "missing": [],
                                "late": [],
                                "__typename": "AssignmentStats"
                            },
                            "sectionStats": [
                                {
                                    "sectionId": "45110000000176720",
                                    "stats": {
                                        "min": 0,
                                        "mean": 94.5945945945946,
                                        "max": 100,
                                        "missing": [],
                                        "late": [],
                                        "__typename": "AssignmentStats"
                                    },
                                    "__typename": "SectionStats"
                                },
                                {
                                    "sectionId": "45110000000176710",
                                    "stats": {
                                        "min": 100,
                                        "mean": 100,
                                        "max": 100,
                                        "missing": [],
                                        "late": [],
                                        "__typename": "AssignmentStats"
                                    },
                                    "__typename": "SectionStats"
                                },
                                {
                                    "sectionId": "45110000000176711",
                                    "stats": {
                                        "min": 100,
                                        "mean": 100,
                                        "max": 100,
                                        "missing": [],
                                        "late": [],
                                        "__typename": "AssignmentStats"
                                    },
                                    "__typename": "SectionStats"
                                },
                                {
                                    "sectionId": "45110000000176714",
                                    "stats": {
                                        "min": 100,
                                        "mean": 100,
                                        "max": 100,
                                        "missing": [],
                                        "late": [],
                                        "__typename": "AssignmentStats"
                                    },
                                    "__typename": "SectionStats"
                                },
                                {
                                    "sectionId": "45110000000176717",
                                    "stats": {
                                        "min": 100,
                                        "mean": 100,
                                        "max": 100,
                                        "missing": [],
                                        "late": [],
                                        "__typename": "AssignmentStats"
                                    },
                                    "__typename": "SectionStats"
                                },
                                {
                                    "sectionId": "45110000000176726",
                                    "stats": {
                                        "min": 0,
                                        "mean": 94.28571428571429,
                                        "max": 100,
                                        "missing": [],
                                        "late": [],
                                        "__typename": "AssignmentStats"
                                    },
                                    "__typename": "SectionStats"
                                },
                                {
                                    "sectionId": "45110000000176723",
                                    "stats": {
                                        "min": 0,
                                        "mean": 94.73684210526316,
                                        "max": 100,
                                        "missing": [],
                                        "late": [],
                                        "__typename": "AssignmentStats"
                                    },
                                    "__typename": "SectionStats"
                                }
                            ],
                            "dueDate": null,
                            "maxScoreRaw": 1,
                            "gradingType": "points",
                            "assignmentType": "ASSIGNMENT",
                            "sectionOverrides": [],
                            "__typename": "Assignment"
                        },
                        "__typename": "AssignmentForCourse"
                    }
                    ...
                ],
                "__typename": "AssignmentForCourseConnection"
            },
            "assignmentsForStudents": [
                {
                    "assignmentId": "45110000001537913",
                    "assignmentName": "Workshop 1",
                    "studentId": "45110000000170594",
                    "cursor": "45110000001537913|45110000000170594|cursor",
                    "dueDate": 1662748200000,
                    "excused": false,
                    "late": false,
                    "missing": false,
                    "submissions": [
                        {
                            "date": null,
                            "gradeRaw": "100",
                            "scoreRaw": 100,
                            "percentage": 100,
                            "__typename": "Submission"
                        }
                    ],
                    "__typename": "StudentAssignment"
                },
                ...
            ],
            "studentInCourseConnection": {
                "edges": [
                    {
                        "currentOverallScore": 99.84,
                        "lastParticipationTime": 1663285505000,
                        "lastPageviewTime": 1663339362000,
                        "sections": [
                            {
                                "id": "45110000000176710",
                                "name": "ME_2004_90428_202209",
                                "__typename": "SectionEnrollment"
                            }
                        ],
                        "student": {
                            "id": "45110000000171296",
                            "studentId": "171296",
                            "studentInfo": {
                                "onTimePercentage": 87.5,
                                "name": "Taiyo Watt",
                                "shortName": null,
                                "sortableName": "Watt, Taiyo",
                                "lastLoggedOut": null,
                                "avatarURL": null,
                                "email": "taiyo@vt.edu",
                                "sisId": "906432220",
                                "__typename": "StudentInfo"
                            },
                            "__typename": "Student"
                        },
                        "__typename": "StudentInCourse"
                    },
                    ...
                ],
                "__typename": "StudentInCourseConnection"
            },
            "__typename": "Course"
        }
    }
}
"""
