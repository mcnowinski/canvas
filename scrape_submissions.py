#!/usr/bin/python3

"""
DESCRIPTION: This script scrapes the Canvas student gradebook for specific entries.
INPUT(S):
    - A class roster CSV file generated using Canvas | New Analytics | Reports | Roster.
"""

import sys
import os
import logging
import requests
import pandas as pd
import json
import time

# configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s',
    handlers=[
        logging.FileHandler("jaisohn.log"),
        logging.StreamHandler()
    ])
logger = logging.getLogger('jaisohn')

# roster CSV file should look like this:
#    Student Name,Student ID,Student SIS ID,Email,Section Name
#    John Doe,203324,906350663,johndoe@vt.edu,ME_2004_90433_202209
#    ...
# path to the roster file
roster_path = './roster.csv'
# canvas add this prefix to the student id provided in the roster list. maybe associated with course?
roster_prefix = '45110000000'

# request parameters
session_id = 'a7fc6d46-a909-4577-bdd8-00a94f299972'
context_id = '7c82cf32d76cd2933b7516aa68c2b8686d6754af'
tc_guid = 'yDz0MxxBs02YM08vCb8fQ85ISbDXw62vLT6KiA6s:canvas-lms'

# assignment name
assignment_name = 'HW 1 Work'

# POST GraphQL query string
# this is a terrible way to do this
graphql_url = 'https://canvas-analytics-iad-prod.inscloudgate.net/v2/graphql'
graphql_headers = {
    'authority': 'canvas-analytics-iad-prod.inscloudgate.net',
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.9',
    'content-type': 'application/json',
    'origin': 'https://canvas-analytics-iad-prod.inscloudgate.net',
    'referer': 'https://canvas-analytics-iad-prod.inscloudgate.net/lti_check_teacher_performance',
    'sec-ch-ua': '"Google Chrome";v="105", "Not)A;Brand";v="8", "Chromium";v="105"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-des': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'session-id': '%s'%session_id,
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36',
    'x-graphql-deduplicate': 'true'
}
graphql_payload_template = '{"operationName":"StudentCourseGradeQuery","variables":{"contextId":"%s",'%context_id + '"tcGuid":"%s",'%tc_guid + '"studentId":"%s'%roster_prefix + 'STUDENT_ID"},"query":"query StudentCourseGradeQuery($contextId: String\u0021, $tcGuid: String\u0021, $studentId: ID\u0021) {course(contextId: $contextId, tcGuid: $tcGuid) {assignmentForCourseConnection {  edges {    assignment {      id      assignmentType      __typename    }    __typename  }  __typename}assignmentsForStudent(id: $studentId) {  assignmentId  assignmentName  studentId  dueDate  submissions {    scoreRaw    percentage    date    __typename  }  excused  missing  late  __typename}studentInCourse(id: $studentId) {  currentOverallScore  sections {    id    name    __typename  }  student {    id    studentInfo {      name      sortableName      shortName      lastLoggedOut      avatarURL      __typename    }    __typename  }  __typename}__typename}}"}'

def main():
    """ the main function """


# does roster file exist?
if not os.path.exists(roster_path):
    sys.exit(f'Roster file ({roster_path}) not found.')

# open and process the roster file
roster = pd.read_csv(roster_path)
# make sure required columns exists
if not 'Student Name' in roster.columns or not 'Student ID' in roster.columns:
    sys.exit(f'Roster file ({roster_path}) format is invalid.')
# build 
for idx in roster.index:
    graphql_json_payload = json.loads(graphql_payload_template.replace('STUDENT_ID', str(roster['Student ID'][idx])))
    response = requests.post(graphql_url, headers=graphql_headers, json=graphql_json_payload)
    data = response.json()
    try:
        assignments = data['data']['course']['assignmentsForStudent']
        for assignment in assignments:
            if assignment['assignmentName'] == assignment_name:
                if assignment['submissions'][0]['date'] != None:
                    print(roster['Student Name'][idx] + ',' + assignment_name + ',' + time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(assignment['submissions'][0]['date']/1000.0)))
    except:
        pass
if __name__ == '__main__':
    main()
